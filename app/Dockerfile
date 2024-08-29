FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
COPY  app.py ${LAMBDA_TASK_ROOT}/
COPY  module.py ${LAMBDA_TASK_ROOT}/
COPY  *.pt ${LAMBDA_TASK_ROOT}/
COPY  *.ttf ${LAMBDA_TASK_ROOT}/


# # Build arguments for AWS credentials
# ARG AWS_ACCESS_KEY_ID
# ARG AWS_SECRET_ACCESS_KEY

# # Use the build arguments in your image as needed
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
ENV MONGO_URL = $MONGO_URL
RUN echo ${MONGO_URL}

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

# Install the specified packages
RUN pip install -r requirements.txt

CMD [ "app.lambda_handler" ]