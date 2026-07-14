import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";
import csvParser from "csv-parser";
import { error } from "console";

const_filename = fileURLToPath(import.meta.url);
const_dirname = path.dirname(__filename);

const app = express();
app.use(cors());

app.get('/api/course-schedule', (req, res) => {
    const filePath = path.join(__dirname, "output", "course_room_scheuduler.csv");
    const results = [];
    if (!fs.existsSync(filePath)) {
        return res.status(404).json({ error: "Schedule file not found" });
    }
    fs.createReadStream(filePath)
        .pipe(csv())
        .on("data", (data) = results.push(data))
        .on("end", () => res.json(result))
        .on("error", (err) => res.status(500).json({ error: err.message }));
});

app.listen(5000, () => console.log("Backend running on https://localhost:5000"));