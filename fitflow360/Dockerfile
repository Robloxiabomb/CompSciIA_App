# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container to /fitflow360
WORKDIR /fitflow360

# Copy all the files from the project's root to the working directory 
COPY app /fitflow360/app/

# Copy the database file
COPY app/user_data.db /fitflow360/app/user_data.db

# Copy the csv file
COPY app/megaGymDataset.csv /fitflow360/app/megaGymDataset.csv

# Check our Python environment
RUN python3 --version && pip3 --version

# Installing Python dependencies 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["python3", "/fitflow360/app/app.py"]
