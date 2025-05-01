module.exports = {
  apps: [
    {
      name: "bioplatform",
      args: "runserver 0.0.0.0:5569",
      script: "manage.py",
      exec_mode: "fork",
      exec_interpreter: ".venv/bin/python"
    }
  ]
} 