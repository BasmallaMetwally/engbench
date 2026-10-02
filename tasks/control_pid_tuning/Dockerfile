FROM python:3.11-slim
RUN pip install --no-cache-dir numpy==1.26.4 scipy==1.13.1
WORKDIR /workspace
COPY README.md example_plant.json sim.py ./
COPY starter/solution.py ./solution.py
# grader.py + reference/ are mounted by the harness only at grading time.
