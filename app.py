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
        # see https://sdk.clams.ai/autodoc/clams.app.html#clams.app.ClamsApp._load_appmetadata
        # Also check out ``metadata.py`` in this directory. 
        # When using the ``metadata.py`` leave this do-nothing "pass" method here. 
        pass

    def _annotate(self, mmif: Union[str, dict, Mmif], **parameters) -> Mmif:

        stitcher = Stitcher(**parameters)
        print('>>>', stitcher)
        predictions = create_predictions(mmif)
        print(f'>>> found {len(predictions)} predictions, printing first five')
        for i in range(5):
            print(f'    {predictions[i]}')
        timeframes = stitcher.create_timeframes(predictions)
        print(f'>>> found {len(timeframes)} timeframes')

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

        # TODO: if no timeframes are added the view metadata will also not have any data
        # in the contains property, don't know whether if this is intentional.

        for tf in timeframes:
            timeframe_annotation = new_view.new_annotation(AnnotationTypes.TimeFrame)
            timeframe_annotation.add_property("label", tf.label),
            timeframe_annotation.add_property('classification', {tf.label: tf.score})
            timepoint_annotations = []
            for prediction in tf.targets:
                timepoint_annotation = new_view.new_annotation(AnnotationTypes.TimePoint)
                timepoint_annotation.add_property('timePoint', prediction.timepoint)
                timepoint_annotation.add_property('label', prediction.label)
                timepoint_annotation.add_property('classification', prediction.classification)
                timepoint_annotations.append(timepoint_annotation)
            timeframe_annotation.add_property(
                'targets', [tp.id for tp in timepoint_annotations])
            reps = [p.annotation.id for p in tf.representative_predictions()]
            timeframe_annotation.add_property("representatives", reps)

        return mmif


def create_predictions(mmif: Mmif):
    predictions = []
    selected_view = None
    for view in mmif.views:
        if view_includes(view, 'TimePoint'):
            selected_view = view
    if selected_view is not None:
        for annotation in selected_view.annotations:
            if '/TimePoint/' in str((annotation.at_type)):
                prediction = Prediction(annotation)
                predictions.append(prediction)
    return predictions


def view_includes(view: View, annotation_type: str):
    for atype in view.metadata.contains.keys():
        # TODO: using the index to get the short name is fragile
        # is there a SDK method that can be used?
        if annotation_type == Path(str(atype)).parts[-2]:
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
