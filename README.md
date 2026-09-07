# 🎮 Combat Arena

**A real-time, browser-based, multiplayer 3D FPS** — two teams (🟦 Allies vs 🟥 Enemies), built with **Django Channels (WebSocket)** on the backend and **Three.js** for 3D rendering.

Spin up the server, share one room code, and play with friends over LAN — **no external game server, no accounts, and no game installation required.**

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Django](https://img.shields.io/badge/django-6.1-092e20)
![Three.js](https://img.shields.io/badge/three.js-r128-black)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

* 🔫 **True 3D first-person shooting** rendered with Three.js — dynamic lighting and shadows, a daylight sky, clouds, trees, and large textured terrain.

* 🧍 **Rigged, animated human characters** — real 3D character models with walk-cycle animations instead of primitive boxes or cylinders.

* 🌐 **Real-time multiplayer over WebSockets** — no bots, no NPCs, only real connected players.

* 🚪 **Shared room-code system** — create or join a room using a shared code, with a real-time lobby that updates instantly without refreshing the page.

* 🟦🟥 **Two-team system** — players can choose between Allies and Enemies, with live team selection and member counts.

* 🔁 **Round-based gameplay** — when one team is completely eliminated, the opposing team wins the round. A **Play Again** button allows the same room to start another round.

* 🎯 **Multiplayer weapon visibility** — players can see weapons held by other players, along with synchronized shooting, muzzle-flash, and hit effects.

* 🔊 **Procedural sound design** — gunfire, hit markers, damage, reload, footsteps, elimination, and round start/end sounds are generated using the **Web Audio API**, with no external audio files.

* ⏸️ **ESC pause menu** — pause the game without leaving the match or disconnecting from the room.

* 🔄 **Self-healing networking** — automatic WebSocket reconnection and periodic state synchronization help recover from temporary network interruptions and prevent permanent desynchronization.

---

## 🧱 Tech Stack

| Layer               | Technology                                                        |
| ------------------- | ----------------------------------------------------------------- |
| Backend             | Django 6.1                                                        |
| Real-time transport | Django Channels + Daphne (ASGI / WebSocket)                       |
| Game frontend       | Three.js r128 — plain JavaScript                                  |
| Character model     | Rigged and animated `Soldier.glb` model from the Three.js project |
| Audio               | Web Audio API — fully synthesized                                 |
| Database            | SQLite                                                            |

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone <this-repo-url>
cd django_project
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run database migrations

```bash
python manage.py migrate
```

### 5. Start the server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

From the home page you can access the build guide at `/guide/` and the game at `/game/`.

---

## 🕹️ Playing Multiplayer Over LAN

Combat Arena is designed to make local multiplayer easy.

To allow other devices on the same Wi-Fi network to connect, start Django on all network interfaces:

```bash
python manage.py runserver 0.0.0.0:8000
```

Find your computer's local IP address.

### Windows

```bash
ipconfig
```

### macOS / Linux

```bash
ifconfig
```

or:

```bash
ip addr
```

For example, if the host computer's local IP is:

```text
192.168.1.100
```

The host can open:

```text
http://127.0.0.1:8000/game/
```

Other players on the same Wi-Fi can open:

```text
http://192.168.1.100:8000/game/
```

> Replace `192.168.1.100` with the host computer's actual local IP address.

### Joining the Same Room

Everyone enters:

* A player name
* The same room code

For example:

```text
Room Code: A7K29
```

Anyone using the same room code will appear in the same live lobby.

Players can then choose:

```text
🟦 Allies
🟥 Enemies
```

Once everyone is ready, any player can press **Start Game**.

---

## 🌐 How Multiplayer Works

The multiplayer system is powered by **Django Channels and WebSockets**.

The browser maintains a WebSocket connection with the Django server to exchange real-time game events such as:

```text
Player Joined
Player Left
Team Changed
Game Started
Player Movement
Player Shooting
Player Hit
Player Eliminated
Round Won
Next Round
```

This allows multiple players to participate in the same live match without constantly refreshing the page.

---

## 🎯 Round System

Each match is divided into rounds.

```text
Players Join
      ↓
Choose Teams
      ↓
Start Game
      ↓
Real-Time Combat
      ↓
One Team Eliminated
      ↓
Round Winner
      ↓
Play Again
      ↓
New Round
```

When all players on one team are eliminated, the opposing team wins the round.

The same room can then be used for another round.

---

## 🔊 Procedural Audio

Combat Arena does not require external audio files for its core sound effects.

Sounds are generated directly in the browser using the **Web Audio API**, including:

* 🔫 Gunfire
* 💥 Hit effects
* ❤️ Damage feedback
* 🔄 Reload sounds
* 👣 Footsteps
* ☠️ Elimination sounds
* 🎮 Round start
* 🏆 Round end

This keeps the project lightweight and self-contained.

---

## 📁 Project Structure

```text
django_project/
│
├── manage.py
├── requirements.txt
├── LICENSE
├── README.md
│
├── mysite/
│   ├── settings.py       # Project settings + Channels configuration
│   ├── asgi.py           # HTTP/WebSocket ASGI routing
│   └── urls.py           # Django URL routing
│
└── core/
    ├── consumers.py      # Room/Team/Round multiplayer logic
    ├── routing.py        # WebSocket URL routing
    ├── views.py
    │
    ├── static/
    │   └── core/
    │       └── models/
    │           └── Soldier.glb
    │
    └── templates/
        └── core/
            ├── home.html
            ├── guide.html # Step-by-step project guide
            └── game.html  # Three.js game + networking
```

---

## ⚠️ Known Limitations

### LAN Multiplayer

The current version is designed primarily for **local network (LAN) multiplayer**.

To play with someone in another house or city, the project would need to be deployed to an internet-accessible server or otherwise configured for secure remote connectivity.

### Client-Side Hit Detection

Hit detection currently begins on the **shooter's browser**.

The server performs basic validation, including checks such as:

* The shooter is alive
* The target is alive
* The players are on opposing teams
* The game is currently active

This approach is suitable for a casual LAN game, but it is **not a fully server-authoritative anti-cheat system**. A determined player could potentially manipulate their own browser-side JavaScript.

A future version could move hit detection and more gameplay validation entirely to the server.

### In-Memory Room State

Room and player state is currently stored in the server process memory.

Therefore, restarting the server will clear active rooms and connected player state.

This is suitable for a lightweight LAN game, but production-scale deployment would benefit from a shared state system such as **Redis**.

---

## 🔮 Future Improvements

Possible future improvements include:

* 🛡️ Server-authoritative hit detection
* 🔐 Stronger anti-cheat protection
* ⚡ Improved network interpolation
* 🎯 More accurate shooting synchronization
* 🗺️ Multiple maps
* 🔫 More weapons
* 💥 Advanced visual effects
* ❤️ Health and HUD improvements
* 🏆 Scoreboard
* 📊 Match statistics
* 🧍 Additional character models and animations
* 🔊 More advanced procedural audio
* 🌍 Internet multiplayer
* 🗄️ Redis-based multiplayer state
* 📱 Mobile controls
* 🏅 Ranking and progression systems

---

## 🤝 Contributing

**Combat Arena is open to contributions!** 🚀

If you're interested in **Django, Django Channels, WebSockets, Three.js, multiplayer games, or browser-based 3D development**, you're welcome to help improve the project.

You can contribute by:

* 🐛 Finding and fixing bugs
* 💡 Suggesting new features
* 🎮 Improving gameplay and multiplayer synchronization
* ⚡ Optimizing performance
* 🎨 Improving the 3D graphics and UI
* 🔊 Improving the procedural audio system
* 🌐 Improving networking and reconnection
* 🛡️ Strengthening server-side validation and anti-cheat systems
* 📝 Improving documentation
* 🔧 Submitting Pull Requests

### How to Contribute

1. Fork the repository.
2. Create a new branch for your change.
3. Make your improvements.
4. Test your changes locally.
5. Commit your changes.
6. Open a Pull Request.

Whether it's a small bug fix or a major new feature, **every contribution is welcome.** ❤️

Let's make Combat Arena better together! 🎮

---

## 📸 Screenshots & Gameplay

Screenshots and gameplay videos can be added here to showcase the game.

Recommended structure:

```text
docs/
├── lobby.png
├── gameplay.png
├── teams.png
└── round.png
```

---

## 📜 Credits & License

The project's own source code is released under the **MIT License**.

See the [`LICENSE`](./LICENSE) file for details.

### Three.js Character Model

The `Soldier.glb` character model is not original to this project.

It is based on the character model included with the official [Three.js](https://github.com/mrdoob/three.js) project and used in its Skinning/Blending example.

The model is distributed according to the applicable Three.js project license.

---

## ⭐ Support the Project

If you find **Combat Arena** interesting or useful, consider giving the repository a ⭐ **Star**.

It helps the project reach more developers interested in:

**Django + Django Channels + WebSockets + Three.js + Multiplayer Game Development**

---

## 🔎 Keywords

`Django` · `Django Channels` · `Three.js` · `WebSocket` · `WebSockets` · `Daphne` · `ASGI` · `Python` · `JavaScript` · `3D Game` · `3D FPS` · `FPS Game` · `Multiplayer Game` · `Multiplayer FPS` · `Real-Time Multiplayer` · `Real-Time Game` · `Browser Game` · `Web Game` · `LAN Game` · `LAN Multiplayer` · `Three.js Game` · `Django Game` · `WebSocket Game` · `Open Source Game`

---

## 🎮 Combat Arena

**Build. Connect. Choose your team. Fight in real time.**
