import express from "express";
import session from "express-session";
import { spawn } from "child_process";
import crypto from "crypto";
import puppeteer from "puppeteer";
import bodyParser from "body-parser";
import bcrypt from "bcrypt";
import { openDB } from "./db.js";

// import hashcash.js
import { verify_pow } from "./hashcash.js";
const BITS = 28;

const app = express();
app.use(bodyParser.json());
app.use(
  session({
    secret: crypto.getRandomValues(new Uint32Array(1))[0].toString(),
    resave: false,
    saveUninitialized: false,
  })
);
app.use((req, res, next) => {
  if (!req.session.pow) {
    // generate 6 random bytes
    req.session.pow = crypto.randomBytes(6).toString("hex");
  }
  next();
});

function requireLogin(req, res, next) {
  if (!req.session.username) {
    return res.status(401).send("Unauthorized");
  }
  next();
}

app.set("view engine", "ejs");

app.get("/", async (req, res) => {
  if (req.session.username) {
    const db = await openDB();
    const notes = await db.all(
      "SELECT title FROM notes WHERE user_id=(SELECT id from users WHERE username=?)",
      [req.session.username]
    );
    res.render("index", { pow: req.session.pow, BITS: BITS, notes: notes });
  } else {
    res.render("login", { pow: req.session.pow, BITS: BITS });
  }
});

app.post("/api/register", async (req, res, next) => {
  try {
    let username = req.body.username;
    let password = req.body.password;

    if (!username || !password) {
      return res
        .status(400)
        .send({ success: false, error: "Missing username or password" });
    }

    password = await bcrypt.hash(password, 10);

    const db = await openDB();
    await db.run("INSERT INTO users (username, password) VALUES (?, ?)", [
      username,
      password,
    ]);

    req.session.username = username;
    res.send({ success: true });
  } catch (e) {
    if (e?.code === "SQLITE_CONSTRAINT") {
      return res
        .status(400)
        .send({ success: false, error: "Username already taken" });
    }
    next(e);
  }
});

app.post("/api/login", async (req, res, next) => {
  try {
    let username = req.body.username;
    let password = req.body.password;

    if (!username || !password) {
      return res
        .status(400)
        .send({ success: false, error: "Missing username or password" });
    }

    const db = await openDB();

    let row = await db.get("SELECT * FROM users WHERE username = ?", [
      username,
    ]);
    if (!row || !(await bcrypt.compare(password, row.password))) {
      return res
        .status(401)
        .send({ success: false, error: "Wrong credentials" });
    }
    req.session.username = username;
    res.send({ success: true });
  } catch (e) {
    next(e);
  }
});

app.post("/api/search", requireLogin, async (req, res, next) => {
  try {
    const title = req.body.title;
    const author = req.body.author;

    if (!title) {
      return res.status(400).send({ success: false, error: "Missing title" });
    }

    const db = await openDB();
    let row;
    if (author) {
      row = await db.get(
        "SELECT title, note FROM notes WHERE title=? AND user_id=(SELECT id from users WHERE username=?) AND public=True",
        [title, author]
      );
    } else {
      row = await db.get(
        "SELECT title, note FROM notes WHERE title=? AND user_id=(SELECT id from users WHERE username=?)",
        [title, req.session.username]
      );
    }
    if (row) {
      res.send({ success: true, note: row });
    } else {
      res.status(404).send({ success: false, error: "Note not found" });
    }
  } catch (e) {
    next(e);
  }
});

app.post("/api/note", requireLogin, async (req, res, next) => {
  try {
    const title = req.body.title;
    const content = req.body.content;
    const is_public = !!req.body.is_public;

    if (!title || !content) {
      return res
        .status(400)
        .send({ success: false, error: "Missing title or note" });
    }

    const db = await openDB();
    await db.run(
      "INSERT INTO notes (title, user_id, note, public) VALUES (?, (SELECT id from users WHERE username=?), ?, ?)",
      [title, req.session.username, content, is_public]
    );

    res.send({ success: true });
  } catch (e) {
    next(e);
  }
});

//headless visit
app.post("/api/report", requireLogin, async (req, res) => {
  if (!req.body.title) {
    return res.status(400).send({ success: false, error: "Missing title" });
  }

  if (!req.body.pow || !verify_pow(BITS, req.session.pow, req.body.pow)) {
    return res.status(400).send({ success: false, error: "Invalid pow" });
  }
  req.session.pow = undefined;

  const username = crypto.randomBytes(14).toString("hex");
  const password = crypto.randomBytes(14).toString("hex");

  (async () => {
    let browser;
    try {
      //start headless browser with puppeteer
      browser = await puppeteer.launch({
        headless: "new",
        executablePath: "/usr/bin/chromium",
        args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu"],
      });
      let page = await browser.newPage();
      await page.goto("http://localhost:3000");
      await page.waitForNetworkIdle();
      await page.type('input[id="username"]', username);
      await page.type('input[id="password"]', password);
      await page.click('button[id="register_btn"]');
      await page.waitForNetworkIdle();

      await page.type(
        'input[id="note_title"]',
        process.env.FLAG || "flag{REDACTED}"
      );
      await page.type('textarea[id="note_content"]', "This is a dummy content");
      await page.click('button[id="note_btn"]');
      await page.waitForNetworkIdle();

      await page.evaluate(
        (title, author) => {
          window.loadNote(title, author);
        },
        req.body.title,
        req.session.username
      );

      await page.waitForNetworkIdle();
    } catch (e) {
      console.log(e);
    } finally {
      if (browser) {
        try {
          await browser.close();
        } catch {}
      }
    }
  })();

  res.send({ success: true, msg: "Headless visit!" });
});

// cleanup dangling chromium processes
setInterval(() => {
  spawn("sh", [
    "-c",
    "ps -eo etime,pid,comm | grep chromium | awk '{if ($1 >= 120) print $2}' | xargs kill -9",
  ]);
}, 60000);

app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).send({ success: false, error: "Internal server error" });
});

app.listen(3000, () => {
  console.log("Server started on http://localhost:3000");
});
