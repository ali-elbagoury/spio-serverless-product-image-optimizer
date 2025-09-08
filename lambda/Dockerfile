FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies (including zip)
RUN yum install -y \
    gcc \
    gcc-c++ \
    make \
    cmake \
    unzip \
    zip \
    libpng-devel \
    libjpeg-turbo-devel \
    libtiff-devel \
    freetype-devel \
    && yum clean all

# Create layer directory structure
WORKDIR /opt
RUN mkdir -p python

# Install NumPy + OpenCV into /opt/python
RUN pip install --no-cache-dir \
    numpy \
    opencv-python-headless \
    -t /opt/python

# Verify install worked (list files)
RUN ls -l /opt/python

WORKDIR /

ENTRYPOINT ["/bin/bash", "-c"]

# Zip layer into /out/layer.zip instead of inside container
CMD ["cd /opt && zip -r9 /out/layer.zip python"]
