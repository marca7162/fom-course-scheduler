import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import csvParser from 'csv-parser';
import { spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());

const outputDir = path.join(__dirname, '..', 'work', 'output');

function sendCsv(res, filename) {
    const filePath = path.join(outputDir, filename);
    const results = [];
    if (!fs.existsSync(filePath)) {
        return res.status(404).json({ error: 'Schedule file not found', file: filePath });
    }
    fs.createReadStream(filePath)
        .pipe(csvParser())
        .on('data', (data) => results.push(data))
        .on('end', () => res.json(results))
        .on('error', (err) => res.status(500).json({ error: err.message }));
}

app.get('/api/course-schedule', (req, res) => {
    sendCsv(res, 'course_room_schedule.csv');
});

app.get('/api/student-schedule', (req, res) => {
    sendCsv(res, 'student_schedule.csv');
});

app.get('/api/teacher-schedule', (req, res) => {
    sendCsv(res, 'teacher_schedule.csv');
});

app.post('/api/run-scheduler', (req, res) => {
    const scriptPath = path.join(__dirname, '..', 'work', 'scripts', 'main.py');
    const py = process.env.PYTHON || 'python';
    const proc = spawn(py, [scriptPath], { cwd: path.join(__dirname, '..'), stdio: ['ignore', 'pipe', 'pipe'] });

    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });

    proc.on('close', (code) => {
        if (code === 0) {
            return res.json({ ok: true, message: 'Scheduler completed', output: stdout });
        } else {
            return res.status(500).json({ ok: false, code, error: stderr || stdout });
        }
    });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Backend running on http://localhost:${PORT}`));