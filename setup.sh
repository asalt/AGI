#!/bin/bash

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Setup R environment (if you use specific R packages)
# Rscript -e 'install.packages(c("ggplot2", "dplyr"), repos="http://cran.us.r-project.org")'
