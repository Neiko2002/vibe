FROM vibe-deg-test:latest

# Clone pyglass (ca. 2-5 MB) and install into the existing Python environment
RUN git clone https://github.com/zilliztech/pyglass /opt/pyglass && \
    cd /opt/pyglass && \
    git config --global --add safe.directory /opt/pyglass && \
    git reset --hard d2296ec447d2374ee8f88c6d3b85be1b1e434ad3 && \
    pip install --no-cache-dir --no-build-isolation -e "python"

WORKDIR /vibe
