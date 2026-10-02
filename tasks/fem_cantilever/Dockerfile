FROM python:3.11-slim
RUN pip install --no-cache-dir numpy==1.26.4 scipy==1.13.1 scikit-fem==12.0.1
# Agent-visible workspace: only the task text, example params and the starter.
WORKDIR /workspace
COPY README.md example_params.json ./
COPY starter/solution.py ./solution.py
# grader/reference are NOT copied: the harness mounts them only at grading time:
#   docker run --rm -v $PWD:/grader:ro -v <workspace>:/workspace IMAGE \
#       python /grader/grader.py /workspace/solution.py
