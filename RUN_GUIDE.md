# 📱 How to Run FinSight AI on Computer & Mobile

Follow these steps to get your project running and accessible on your phone.

## 1. Preparation
Ensure both your **Mac** and your **Phone** are connected to the **SAME Wi-Fi network**.

## 2. Start the Servers
Open your terminal on the Mac, navigate to the project folder, and run:

```bash
./run_project.sh
```

## 3. Access the Project

### On your Mac:
The script will automatically open your browser to:
`http://localhost:5000/index.html`

### On your Phone:
1. Look at the terminal output after running the script.
2. It will show a "MOBILE" link like `http://192.168.x.x:5000/index.html`.
3. Open the browser on your phone (Safari or Chrome) and type that address.

---

## 🛠️ Troubleshooting

- **Connection Failed?** Double check that your phone's Wi-Fi is the same as your Mac's.
- **Port Error?** The script automatically tries to clear ports 5000 and 8000. If it fails, you can try running `killall python3` in your terminal.
- **Firewall?** If your Mac firewall is on, it might block the incoming connection from your phone. You may need to allow Python to accept incoming connections in *System Settings > Network > Firewall*.
