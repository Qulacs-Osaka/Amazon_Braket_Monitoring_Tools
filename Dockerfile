FROM python:3.8.2-buster
MAINTAINER Sergio Martinez-Losa

ENV DEBIAN_FRONTEND noninteractive

ENV BRAKET_USER=braket

# CREATE NEW USER
RUN useradd --create-home -s /bin/bash $BRAKET_USER
ENV BRAKET_DIR=/home/$BRAKET_USER

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y build-essential poppler-utils apt-utils texlive-latex-base texlive-latex-extra libopenblas-dev \
                       sudo unzip wget nano poppler-utils cmake git libssl-dev zlib1g-dev libncurses5-dev libgdbm-dev \
                       libnss3-dev libssl-dev libreadline-dev libffi-dev curl libsqlite3-dev curl unzip

WORKDIR $BRAKET_DIR

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip3 install pip==20.3.1

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && \
    sudo ./aws/install && /usr/local/bin/aws --version

RUN pip3 install boto3
#RUN pip3 install amazon-braket-sdk
RUN git clone https://github.com/aws/amazon-braket-sdk-python.git && cd amazon-braket-sdk-python && \
    pip install .

RUN pip3 install dwave-ocean-sdk amazon-braket-ocean-plugin jupyterlab amazon-braket-pennylane-plugin

# FINISHING PACKAGES
RUN pip install keras pandas xlrd seaborn scikit-learn matplotlib opencv-python tqdm pillow \
                image scipy regex cffi pylatexenc tikz2graphml plotly==4.14.1 --use-deprecated=legacy-resolver

#RUN mkdir -p aws-braket-jupyter && cd aws-braket-jupyter &&  git clone https://github.com/aws/amazon-braket-examples.git

# SET ROOT PERMISSION FOR ALL USERS
RUN chown -R $BRAKET_USER:$BRAKET_USER /home/$BRAKET_USER/
RUN usermod -aG sudo $BRAKET_USER
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# CHANGE TO NEW USER
USER $BRAKET_USER

# RUN JUPYTER ON PORT 8889
#CMD [ "jupyter" , "notebook",  "--ip=0.0.0.0", "--port=8889", "--notebook-dir=./aws-braket-jupyter", "--no-browser" ]
CMD ["/bin/bash"]
# Get the jupyter token : docker logs -f <NAME_OF_THIS_IMAGE>
