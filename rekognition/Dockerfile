FROM public.ecr.aws/lambda/python:3.10-x86_64

# Copy requirements.txt and Python scripts to the container
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
COPY *.py ${LAMBDA_TASK_ROOT}/
ENV MONGO_URL = $MONGO_URL
RUN pip install -r requirements.txt

CMD [ "app.rekognition_handler" ]