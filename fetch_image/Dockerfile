FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
COPY  *.py ${LAMBDA_TASK_ROOT}/

# Set environment variables to disable GPU usage
ENV CUDA_VISIBLE_DEVICES=""
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY

RUN yum install -y \
    gcc \
    gcc-c++ \
    cmake \
    git \
    wget \
    unzip \
    libjpeg-devel \
    libpng-devel \
    libtiff-devel \
    jasper-devel \
    openexr-devel \
    libwebp-devel \
    libcurl-devel \
    libglu-devel \
    mesa-libGLU \
    mesa-libGL \
    glibc-static \
    mesa-libEGL \
    libGLU.so.1 \
    libjpeg \
    libpng

RUN mkdir -p /root/.deepface
RUN mkdir -p /root/.deepface/weights/
COPY openface_weights.h5 /root/.deepface/weights/openface_weights.h5

RUN pip install -r requirements.txt

CMD [ "app.fetch_image_handler" ]