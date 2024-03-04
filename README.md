# Stitcher

<span style="color:red">This prototype is awaiting a new version of clams-python. As you can see in the requirements file, the version specified is 1.1.2, but that one was recently retracted.</span>

Standalone Stitcher that can be used on the output of the SWT app as long as it was run using the useStitcher parameter set to False (this is needed for two reasons: one is to make sure all TimePoints are availabel and the other is that this prototpye is somewhat simplistic in how it selects its input view).

To run the stitcher you first edit `stitcher/config.py`, in particular, the label_mapping needs to be updated to reflect the kind of mappings that you want to use.

Use a fairly recent Python version and install the requirements:

```bash
$ pip install -r requirements.txt
```

To start the server just type `python app.py` and to process a MMIF file do

```bash
$ curl -X POST -d@data/example-mmif.json "http://localhost:5000?pretty=1"
```

You can use the example file even if you do not have the video file since the code does not require access to the source data.

The output will have TimeFrames, just like the SWT app:

```json
{
    "@type": "http://mmif.clams.ai/vocabulary/TimeFrame/v2",
    "properties": {
      "label": "slate",
      "classification": {"slate": 0.9825162668334894},
      "targets": ["tp_31", "tp_32", "tp_33", "tp_34", "tp_35", "tp_36", 
                  "tp_37", "tp_38", "tp_39", "tp_40", "tp_41"],
      "representatives": ["tp_39"],
      "id": "tf_2"
}
```  

All TimePoints included in the TimeFrame are also in the output, for example:

```json
{
    "@type": "http://mmif.clams.ai/vocabulary/TimePoint/v1",
    "properties": {
        "timePoint": 30000,
        "label": "slate",
        "classification": {
            "bars": 1.720956788631156e-05,
            "slate": 0.9821906582050133,
            "chyron": 0.00016418585801147856,
            "credits": 8.137159056786913e-06 },
        "targets": ["v_0:tp_31"],
        "id": "tp_31"
}
```

The targets property contains the TimePoint from the SWT view, which will have a classification with all the pre-bin labels.


### CLAMS Note

At the moment this app is not intended to ever be released as an official CLAMS App due to worries on whether it can ever be framed as a truly independent app. In particular, the app relies on a rather complex category mapping that with the current implementation of CLAMS cannot be nicely handled.
