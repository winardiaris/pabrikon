FROM python:3.12-slim

WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["pabrikon"]
CMD ["--help"]
