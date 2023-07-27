BUILDSTAMP_FILE = docker-buildstamp
IMAGE = scrollscraper

.PHONY: all
all: $(BUILDSTAMP_FILE)

test: $(BUILDSTAMP_FILE)
	docker run -v `pwd`/state:/state -w /var/opt/scrollscraper -i -t $(IMAGE) /bin/bash -c "make test-scrollscraper.html; cat test-scrollscraper.html"

test-mp3: download-mp3s $(BUILDSTAMP_FILE)
	mkdir -p state/smil
	touch state/smil/daystampAndLock.txt
	docker run -v `pwd`/local_ort_mp3s:/ort_mp3s -v `pwd`/state:/state -w /var/opt/scrollscraper -i -t $(IMAGE) /bin/bash -c "make test-scrollscraper.mp3"

clean-dataprep: $(BUILDSTAMP_FILE)
	docker run -w /var/opt/scrollscraper -t $(IMAGE) /bin/bash -c "cd scrollscraper; make clean-scrollscraper-data; make test-scrollscraper.html"

$(BUILDSTAMP_FILE): Dockerfile scrollscraper.cgi buildmp3.cgi Makefile
	docker build -t $(IMAGE) .
	mkdir -p state/smil
	touch state/smil/daystampAndLock.txt
	touch $@

download-mp3s:
	mkdir -p local_ort_mp3s
	docker run -v `pwd`/local_ort_mp3s:/ort_mp3s -w /var/opt/scrollscraper -i -t scrollscraper /bin/bash -x utilities/fetchMP3s.sh
	touch $@

clean:
	docker image rm -f $(IMAGE)
	rm -f $(BUILDSTAMP_FILE)


#======== Makefile targets to be run within the scrollscraper container appear below ==========

intermediate_outputs/gif_names.txt:
	find webmedia/ -name \*.gif | sort | sed "s/^/\//" >$@

final_outputs/gif_info.csv: intermediate_outputs/gif_names.txt
	@echo This command could take 5 minutes or so to run.  Be patient.
	perl utilities/gifETL.pl <$< >$@

intermediate_outputs/color_analysis.csv: intermediate_outputs/gif_names.txt
	@echo This command could take 8 minutes or so to run.  Be patient.
	perl utilities/gifETL2.pl <$< >$@

intermediate_outputs/augmented_color_analysis_with_verses.csv: intermediate_outputs/color_analysis.csv final_outputs/gif_info.csv
	grep -v BOOK,CHAPTER <$< | perl utilities/gifETL3.pl >$@

final_outputs/map.csv: intermediate_outputs/augmented_color_analysis_with_verses.csv utilities/handCuration.sed
	sed -f utilities/handCuration.sed <$< >$@

clean-scrollscraper-data:
	rm -f intermediate_outputs/* final_outputs/*

otherComputedPNGs/sampleTorahMap.png: utilities/generateSampleTorahMap.pl final_outputs/map.csv
	grep t2/1601C101.gif final_outputs/map.csv |  perl utilities/generateSampleTorahMap.pl >$@

test-scrollscraper.html: final_outputs/map.csv final_outputs/gif_info.csv
	perl scrollscraper.cgi "book=5&audioRepeatCount=1&coloring=0&doShading=on&startc=32&startv=35&endc=32&endv=45&dontUseCache=1&trueTypeFonts=1" >$@

test-scrollscraper.mp3: buildmp3.cgi
	mkdir -p scrollscraperWorkingDir smil
	touch smil/daystampAndLock.txt
	perl buildmp3.cgi "flags=41&book=5&startc=32&endc=32&startv=35&endv=45&audioRepeatCount=2&raFiles="
