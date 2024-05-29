FROM continuumio/miniconda3

WORKDIR /usr/app

ADD environment.yml environment.yml
ADD bot.py bot.py
ADD audio_processing.py audio_processing.py
ADD init.sh init.sh

RUN conda env create --name slorev --file environment.yml

RUN /bin/bash init.sh

# for a more robust way to utilize Conda in Docker, read:
# https://pythonspeed.com/articles/activate-conda-dockerfile/
# but for now let's stick to a "portable" solution 
ENTRYPOINT ["conda", "run", "--no-capture-output", "--name", "slorev", "python", "bot.py"]
