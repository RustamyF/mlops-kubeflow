FROM public.ecr.aws/j1r0q0g6/notebooks/notebook-servers/jupyter:v1.5.0

USER root

RUN pip3 install tensorflow-datasets==2.1.0 \
                 scikit-learn==1.1.0 \
                 pandas==1.0.3
ENV NB_PREFIX /
