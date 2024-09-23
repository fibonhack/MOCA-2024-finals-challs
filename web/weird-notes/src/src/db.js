// sqlite database
import sqlite3 from "sqlite3";
import { open } from "sqlite";

export async function openDB() {
  const db = await open({
    filename: "./db.sqlite",
    driver: sqlite3.cached.Database,
  });

  // init tables
  await Promise.all([
    db.run(
      "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)"
    ),
    db.run(
      "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, user_id INTEGER, note LONG TEXT, public BOOLEAN DEFAULT(0), UNIQUE(title, user_id))"
    ),
  ]);

  return db;
}
