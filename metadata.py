"""

Metadata for the Stitcher prototype.

"""

from mmif import DocumentTypes, AnnotationTypes

from clams.app import ClamsApp
from clams.appmetadata import AppMetadata


def appmetadata() -> AppMetadata:
    
    metadata = AppMetadata(
        name="Stitcher",
        description="Stitching TimePoints together into TimeFrames",
        app_license="Apache 2.0",
        identifier="prototype-stitcher",
        url="https://github.com/clamsproject/app-stitcher",
        analyzer_license="Apache 2.0"
    )

    metadata.add_input(AnnotationTypes.TimePoint)
    metadata.add_output(AnnotationTypes.TimePoint)
    metadata.add_output(AnnotationTypes.TimeFrame)

    metadata.add_parameter(
        name='minFrameScore', type='number', default=0.01,
        description='minimum score for a TimePoint')
    metadata.add_parameter(
        name='minTimeFrameScore', type='number', default=0.5,
        description='minimum score for a TimeFrame')
    metadata.add_parameter(
        name='minFrameCount', type='number', default=2,
        description='minimum number of still frames in a TimeFrame')

    return metadata


# DO NOT CHANGE the main block
if __name__ == '__main__':
    import sys
    metadata = appmetadata()
    for param in ClamsApp.universal_parameters:
        metadata.add_parameter(**param)
    sys.stdout.write(metadata.jsonify(pretty=True))
