# Browser Bot

This project aims at running an agent that can browse the web and perform actions on it.

## Prerequisites

- Docker and Docker Compose

## Project Structure

- `docker-compose.yml`: Configuration file for launching the container.
- `src/main.py`: Main script for managing the container and processes.
- `src/log_server.py`: Server to stream logs via a web interface.
- `.env`: Environment configuration file.

## Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/CaptainIgl00/browser_bot.git
   ```

2. Navigate to the project directory:
   ```bash
   cd browser_bot
   ```

3. Add your DeepSeek API key to the `.env` file.

    ```bash
    DEEPSEEK_API_KEY=your_api_key
    ```

4. Launch Docker Compose:
   ```bash
   docker-compose up --build
   ```

5. Access the VNC interface via `http://localhost:8080`.

## License

This project is licensed under the MIT License.
