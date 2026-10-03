FROM python:3.11-slim
RUN pip install --no-cache-dir numpy
WORKDIR /workspace
COPY README.md example_data.json ./
COPY starter/solution.py ./solution.py
CMD ["bash"]
