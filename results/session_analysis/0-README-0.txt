naming convention is as follows:

<x-axis mode>_avg_<session type>_sessions_<bin size>.<file type>

x-axis mode:
	TIME	axis is time, in minutes (from beginning of session for non-adopt, first adoption event if adopt)
	NORM	axis is normalized (before average) time
			non-adopt normalizes all sessions to 0-100
			adopt normalizes commits before the first adoption to -100-0, and post-adopt commits to 0-100

session type:
	adopt		sessions containing at least one adoption event
	non-adopt	sessions containing no adoption events

bin size:
	for TIME results, the width of the combination bin in minutes
	for NORM results, the width of the bin in % of the entire session length