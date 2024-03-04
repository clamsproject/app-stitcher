"""

Stitcher prototype.

"""

import argparse
import logging
from pathlib import Path
from typing import Union

from clams import ClamsApp, Restifier
from mmif import Mmif, View, Annotation, Document, AnnotationTypes, DocumentTypes

from stitcher import Stitcher, Prediction


class StitcherApp(ClamsApp):

    def __init__(self):
        super().__init__()

    def _appmetadata(self):
        # do not remove this method
        pass

    def _annotate(self, mmif: Union[str, dict, Mmif], **parameters) -> Mmif:

        stitcher = Stitcher(**parameters)
        predictions = create_predictions(mmif)
        timeframes = stitcher.create_timeframes(predictions)

        vds = mmif.get_documents_by_type(DocumentTypes.VideoDocument)
        vd = vds[0]
        new_view: View = mmif.new_view()
        self.sign_view(new_view, parameters)
        labelset = list(stitcher.label_mapping.keys())
        new_view.new_contain(
            AnnotationTypes.TimeFrame,
            document=vd.id, timeUnit='milliseconds', labelset=labelset)
        new_view.new_contain(
            AnnotationTypes.TimePoint,
            document=vd.id, timeUnit='milliseconds', labelset=labelset)
        
        # NOTE. If no timeframes are added the view metadata will also not have any data
        # in the contains property. This is because CLAMSApp.annotate() serializes using
        # sanitize=True and Mmif.sanitize() removes annotations types from the metadata
        # if none were found.

        for tf in timeframes:
            timeframe_annotation = new_view.new_annotation(AnnotationTypes.TimeFrame)
            timeframe_annotation.add_property("label", tf.label),
            timeframe_annotation.add_property('classification', {tf.label: tf.score})
            timepoint_annotations = []
            for prediction in tf.targets:
                target = f'{prediction.view_id}:{prediction.id}'
                tp_annotation = new_view.new_annotation(AnnotationTypes.TimePoint)
                tp_annotation.add_property('timePoint', prediction.timepoint)
                tp_annotation.add_property('label', prediction.label)
                tp_annotation.add_property('classification', prediction.classification)
                tp_annotation.add_property('targets', [target])
                timepoint_annotations.append(tp_annotation)
            timeframe_annotation.add_property(
                'targets', [tp.id for tp in timepoint_annotations])
            reps = [p.annotation.id for p in tf.representative_predictions()]
            timeframe_annotation.add_property("representatives", reps)

        return mmif


def create_predictions(mmif: Mmif):
    """Creates predictions from the TimePoints."""
    predictions = []
    selected_view = None
    for view in mmif.views:
        if view_includes(view, 'TimePoint'):
            selected_view = view
    if selected_view is not None:
        for annotation in selected_view.annotations:
            if '/TimePoint/' in str((annotation.at_type)):
                prediction = Prediction(annotation, selected_view.id)
                predictions.append(prediction)
    return predictions


def view_includes(view: View, annotation_type: str):
    """Returns True if the annotation type is included in the view's metadata."""
    for atype in view.metadata.contains.keys():
        if annotation_type in Path(str(atype)).parts:
            return True
    return False


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", action="store", default="5000", help="set port to listen")
    parser.add_argument("--production", action="store_true", help="run gunicorn server")
    parsed_args = parser.parse_args()

    app = StitcherApp()

    http_app = Restifier(app, port=int(parsed_args.port))
    if parsed_args.production:
        http_app.serve_production()
    else:
        app.logger.setLevel(logging.DEBUG)
        http_app.run()
