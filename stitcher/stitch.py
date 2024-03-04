"""Stitching module

Used by app.py in the parent directory and by the modeling.classify is it is used
in standalone mode.

See app.py for hints on how to uses this, the main method is create_timeframes(),
which takes a list of predictions from the classifier and creates TimeFrames.

"""


import operator
import yaml
from mmif import Annotation
from stitcher import config


class Stitcher:

    def __init__(self, **parameters):
        # get default settings from the config, but allow some of them (for now
        # perhaps) to be overwritten by the parameters
        print("parameters:", parameters)
        self.min_frame_score = config.min_frame_score
        self.min_timeframe_score = config.min_timeframe_score
        self.min_frame_count = config.min_frame_count
        self.static_frames = config.static_frames
        self.label_mapping = config.label_mapping
        if parameters.get("minFrameScore"):
            self.min_frame_score = parameters.get("minFrameScore")
        if parameters.get("minTimeFrameScore"):
            self.min_timeframe_score = parameters.get("minTimeFrameScore")
        if parameters.get("minFrameCount"):
            self.min_frame_count = parameters.get("minFrameCount")
        #if parameters.get("staticFrames"):
        #    self.static_frames = parameters.get("staticFrames")
        #if parameters.get("labelMapping"):
        #    self.label_mapping = parameters.get("labelMapping")
        self.debug = True

    def __str__(self):
        return (f'<Stitcher min_frame_score={self.min_frame_score} '
                + f'min_timeframe_score={self.min_timeframe_score} '
                + f'min_frame_count={self.min_frame_count}>')

    def create_timeframes(self, predictions: list) -> list:
        timeframes = self.collect_timeframes(predictions)
        #if self.debug:
        #    print_timeframes('Collected frames', timeframes)
        timeframes = self.filter_timeframes(timeframes)
        if self.debug:
            print_timeframes('Filtered frames', timeframes)
        timeframes = self.remove_overlapping_timeframes(timeframes)
        for tf in timeframes:
            tf.set_representatives()
        timeframes = list(sorted(timeframes, key=(lambda tf: tf.start)))
        if self.debug:
            print_timeframes('Final frames', timeframes)
        return timeframes

    def collect_timeframes(self, predictions: list) -> list:
        """Find sequences of frames for all labels where the score of each frame
        is at least the mininum value as defined in self.min_frame_score. Also
        make sure that the sequence contains at least two still frames."""
        if self.label_mapping:
            for prediction in predictions:
                prediction.create_bins(self.label_mapping)
        labels = predictions[0].labels()
        timeframes = []
        open_frames = { label: TimeFrame(label, self) for label in labels}
        for prediction in predictions:
            for label in prediction.classification:
                score = prediction.score_for_label(label)
                if score < self.min_frame_score:
                    # the second part checks whether there is something in the timeframe
                    if open_frames[label] and open_frames[label][0]:
                        timeframes.append(open_frames[label])
                    open_frames[label] = TimeFrame(label, self)
                else:
                    open_frames[label].add_prediction(prediction, score)
        for label in labels:
            if open_frames[label]:
                timeframes.append(open_frames[label])
        for tf in timeframes:
            tf.finish()
        timeframes = [tf for tf in timeframes if len(tf) > 1]
        return timeframes

    def filter_timeframes(self, timeframes: list) -> list:
        """Filter out all timeframes with an average score below the threshold defined
        in the configuration settings."""
        # TODO: this now also uses the minimum number of samples, but maybe do this
        # filtering later in case we want to use short competing timeframes as a way
        # to determine whether another timeframe is viable
        return [tf for tf in timeframes
                if (tf.score > self.min_timeframe_score
                    and len(tf) >= self.min_frame_count)]

    def remove_overlapping_timeframes(self, timeframes: list) -> list:
        all_frames = list(sorted(timeframes, key=lambda tf: tf.score, reverse=True))
        outlawed_timepoints = set()
        final_frames = []
        for frame in all_frames:
            if self.is_included(frame, outlawed_timepoints):
                continue
            final_frames.append(frame)
            for pred in frame.targets:
                outlawed_timepoints.add(pred.timepoint)
        return final_frames

    def is_included(self, frame, outlawed_timepoints: set) -> bool:
        for pred in frame.targets:
            if pred.timepoint in outlawed_timepoints:
                return True
        return False


class Prediction:

    """Convenience object that wraps a MMIF Annotation and makes the information
    needed for stitching readily available.

    view_id         -  the identifier of the view that the Annotation is from
    timepoint       -  the location of the frame in the video, in milliseconds
    label           -  highest scoring label for the annotation
    score           -  score of the label
    classification  -  scores for all labels
    annotation      -  the wrapped MMIF annotation

    """

    def __init__(self, annotation: Annotation, view_id: str):
        self.annotation = annotation
        self.id = annotation.id
        self.view_id = view_id
        self.timepoint = annotation.get_property('timePoint')
        self.label = annotation.get_property('label')
        self.classification = annotation.get_property('classification')
        self.score = self.classification.get(self.label)

    def __str__(self):
        return (f'<Prediction view={self.view_id} id={self.id}'
                + f' timepoint={self.timepoint}'
                + f' label={self.label} score={self.score:.2f}>')

    def labels(self):
        return list(self.classification.keys())

    def score_for_label(self, label: str):
        """Return the score for a label."""
        return self.classification.get(label)

    def create_bins(self, label_mapping: dict):
        """Overwrite the classification with a binned classification, also updates
        the label and the score."""
        binned_classification = {}
        for post_label, pre_labels in label_mapping.items():
            binned_classification[post_label] = 0
            for pre_label in pre_labels:
                binned_classification[post_label] += self.classification[pre_label]
        self.classification = binned_classification
        self.label = max(self.classification, key=self.classification.get)
        self.score = self.classification[self.label]


class TimeFrame:

    def __init__(self, label: str, stitcher: Stitcher):
        self.static_frames = stitcher.static_frames
        self.targets = []
        self.label = label
        self.points = []
        self.scores = []
        self.representatives = []
        self.start = None
        self.end = None
        self.score = None

    def __len__(self):
        return len(self.targets)

    def __nonzero__(self):
        return len(self) != 0

    def __getitem__(self, item: int):
        return self.targets[item]

    def __str__(self):
        if self.is_empty():
            return "<TimePoint empty>"
        else:
            score = -1 if self.score is None else self.score
            span = f"{self.points[0]}:{self.points[-1]}"
            return f"<TimeFrame {self.label} {span} score={score:0.4f}>"

    def add_prediction(self, prediction, score):
        self.targets.append(prediction)
        self.points.append(prediction.timepoint)
        self.scores.append(score)
        #print(f"{prediction} {score:.4f} ==> {self}")

    def finish(self):
        """Once all points have been added to a timeframe, use this method to
        calculate the timeframe score from the points and to set start and end."""
        self.score = sum(self.scores) / len(self)
        self.start = self.points[0]
        self.end = self.points[-1]

    def is_empty(self) -> bool:
        return len(self) == 0

    def representative_predictions(self) -> list:
        answer = []
        for rep in self.representatives:
            for pred in self.targets:
                if pred.timepoint == rep:
                    answer.append(pred)
        return answer

    def set_representatives(self):
        """Calculate the representative still frames for the time frame, using a
        couple of simple heuristics and the frame type."""
        representatives = list(zip(self.points, self.scores))
        timepoint, max_value = max(representatives, key=operator.itemgetter(1))
        if self.label in self.static_frames:
            # for these just pick the one with the highest score
            self.representatives = [timepoint]
        else:
            # throw out the lower values
            representatives = [(tp, val) for tp, val in representatives if val >= self.score]
            # pick every third frame, which corresponds roughly to one every five seconds
            # (expect when all below-average values bundled together at one end)
            representatives = representatives[0::3]
            self.representatives = [tp for tp, val in representatives]

    def pp(self):
        print(self)
        print('  ', self.points)
        print('  ', self.scores)
        print('  ', self.representatives)


def print_timeframes(header, timeframes: list):
    print(f'\n{header} ({len(timeframes)})')
    for tf in sorted(timeframes, key=lambda tf: tf.start):
        print(tf)
