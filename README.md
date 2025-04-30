# Movie Recommendation DevOps Project

This project demonstrates setting up a Python-based Movie Recommendation application using Docker, Docker Compose, Nginx, and defining a basic CI/CD pipeline configuration, fulfilling the requirements of the DevOps course project.

## Project Structure

movie-rec-devops/

├── actual_app/        
│   ├── templates/     
│   │   ├── index.html
│   │   └── recommendations.html
│   ├── app.py         
│   └── cleaned_I_THINK.csv 
├── nginx/
│   └── nginx.conf       
├── Dockerfile            
├── docker-compose.yml    
├── .gitlab-ci.yml        
├── requirements.txt      
└── README.md             

## How to Run Locally

1.  **Prerequisites:** Make sure you have Docker and Docker Compose installed ([https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)).
2.  **Clone the repository (Optional if you already have it):**
    ```bash
    git clone [https://github.com/Nurlybek1-cpu/movie-recommendation-devops.git](https://github.com/Nurlybek1-cpu/movie-recommendation-devops.git)
    cd movie-recommendation-devops
    ```
3.  **Build and Run Containers:** Open a terminal in the project's root directory (`movie-rec-devops/`) and run:
    ```bash
    docker-compose up --build -d
    ```
    * `--build`: Builds the application image based on the `Dockerfile`.
    * `-d`: Runs the containers in detached mode (in the background).
4.  **Access the Application:** Open your web browser and navigate to:
    * `http://localhost:5000` (Or replace `5000` with the host port you configured in `docker-compose.yml` if you changed it).

5.  **Stop the Containers:** To stop the running containers, run:
    ```bash
    docker-compose down
    ```

## Fulfilling Project Requirements

1.  **Build a project in Docker:** The `Dockerfile` defines the image for the Python application, and `docker-compose.yml` builds and runs it.
2.  **Give rights:** The `Dockerfile` creates a non-root user (`appuser`) and runs the application under this user for improved security (`USER appuser`, `chown`).
3.  **Make CI/CD:** The `.gitlab-ci.yml` file defines a pipeline to build the Docker image and push it to a container registry upon code changes (demonstrating CI/CD configuration).
4.  **More than 1 container with connection:** `docker-compose.yml` defines two services (`app` and `nginx`). They communicate over a custom Docker network (`app-network`), with Nginx acting as a reverse proxy for the `app` service.
5.  **Add topic from syllabus:** This project incorporates **Nginx** (Week 5: Traffic Management) as a reverse proxy. It also utilizes concepts from Week 4 (Docker, Dockerfile, Docker Compose, Docker Networks) and Week 2 (Permissions).

