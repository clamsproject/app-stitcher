# Stitcher notes

Requirements: 

```bash
$ pip install clams-python==1.1.2
$ pip install pyyaml==6.0.1
```

Amongst many other things clams-python installs mmif-python==1.0.9.


## Running the application

To build the Docker image and run the container

```bash
docker build -t app-stitcher -f Containerfile .
docker run --rm -d -v /Users/Shared/archive/:/data -p 5000:5000 app-stitcher
```

The path `/Users/Shared/archive/` should be edited to match your local configuaration.

Processing a MMIF file:

```bash
curl -X POST -d@data/example-mmif.json http://localhost:5000/
```

This may take a while depending on the size of the video file embedded in the MMIF file. It should return a MMIF object with TimeFrame and TimePoint annotations added.


## The Stitcher and the apps directory

This app is not intended to be released officially in https://apps.clams.ai/, for that reason there are no github actions in this repository.


## Miscellaneous

In `stitcher.config` we have a label mapping and that is input to the stitcher. From a CLAMMS App 
# This is not good App practice since it would hard-wire the app to this default
# and overruling them with a parameter is cumbersome. Nevertheless doing this for
# now because (a) this does not need to be a well-behaved and published app and
# we will most likely run this locally, and (b) it is the quickest way to get
# something to work.

## Comments on the skeleton

To be entered as issues in https://github.com/clamsproject/clams-python.

Script metadata.py:

- Comment on analyzer_version should make it clear that it should be deleted if we are not wrapping something.

- Refers to .github/README.md, which does not exist.

- Typo in "    # metadta.add_parameter(more...)"
