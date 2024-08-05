FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
COPY  *.py ${LAMBDA_TASK_ROOT}/

RUN pip install -r requirements.txt

CMD [ "app.fetch_image_handler" ]