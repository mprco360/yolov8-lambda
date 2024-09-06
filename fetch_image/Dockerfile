# Use the AWS Lambda base image for Python 3.11
FROM public.ecr.aws/lambda/python:3.10-x86_64

# Copy requirements.txt and Python scripts to the container
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
COPY *.py ${LAMBDA_TASK_ROOT}/

RUN yum -y update && \
    yum install -y \
    make \
    cmake \
    gcc \
    gcc-c++ \
    git \
    wget \
    curl \
    graphicsmagick \
    libgraphicsmagick-devel \
    atlas-devel \
    libavcodec-devel \
    libavformat-devel \
    gtk2-devel \
    libjpeg-devel \
    lapack-devel \
    libswscale-devel \
    pkgconfig \
    python3-devel \
    python3-numpy \
    zip

RUN cd ~ && \
    mkdir -p dlib && \
    git clone -b 'v19.9' --single-branch https://github.com/davisking/dlib.git dlib/ && \
    cd dlib/ && \
    mkdir build && cd build && \
    cmake .. -DDLIB_USE_CUDA=0 -DUSE_AVX_INSTRUCTIONS=1 && \
    cmake --build . && \
    cd .. && \
    python3 setup.py install --yes USE_AVX_INSTRUCTIONS
# Install Python packages from requirements.txt

RUN pip install -r requirements.txt

# Command to run the Lambda function
CMD [ "app.fetch_image_handler" ]