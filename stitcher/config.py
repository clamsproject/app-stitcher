
negative_label = 'NEG'

# Mapping from post-bin to pre-bin labels
label_mapping = {
	"bars": ['B'],
    "slate": ['S', 'S:H', 'S:C', 'S:D', 'S:G'],
    "chyron": ['I', 'N', 'Y'],
    "credits": ['C']
}

# Minimum score for a frame to be included in a potential timeframe
min_frame_score = 0.01

# Minimum score for a timeframe to be selected
min_timeframe_score = 0.5

# Minimum number of sampled frames required for a timeframe to be included
min_frame_count = 2

# These are time frames that are typically static (that is, the text does not
# move around or change as with rolling credits)
static_frames = ["bars", "slate", "chyron"]
