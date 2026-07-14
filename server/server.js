import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import csvParser from 'csv-parser';
import { spawn } from 'child_process';

let latestCandidates = [];
let latestSelectedSchedule = [];

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

function writeCsvFile(filePath, rows, headers) {
    const lines = [headers.join(',')];
    rows.forEach((row) => {
        const values = headers.map((header) => {
            const value = row[header] ?? '';
            return String(value).replace(/"/g, '""');
        });
        lines.push(values.map((value) => `"${value}"`).join(','));
    });
    fs.writeFileSync(filePath, lines.join('\n'));
}

function writeSelectedSchedule(candidate) {
    const courseRows = candidate.rows || [];
    const teacherRows = [];
    const studentRows = [];

    courseRows.forEach((row) => {
        teacherRows.push({
            teacherName: 'Unknown',
            day: row.day,
            period: row.period,
            courseCode: row.courseCode,
            roomNumber: row.roomNumber,
        });
    });

    writeCsvFile(path.join(outputDir, 'course_room_schedule.csv'), courseRows, ['courseCode', 'day', 'period', 'roomNumber']);
    writeCsvFile(path.join(outputDir, 'teacher_schedule.csv'), teacherRows, ['teacherName', 'day', 'period', 'courseCode', 'roomNumber']);
    writeCsvFile(path.join(outputDir, 'student_schedule.csv'), studentRows, ['studentId', 'courseCode', 'day', 'period', 'roomNumber']);
    latestSelectedSchedule = courseRows;
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
    const proc = spawn(py, [scriptPath, '--json'], { cwd: path.join(__dirname, '..'), stdio: ['ignore', 'pipe', 'pipe'] });

    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });

    proc.on('close', (code) => {
        if (code === 0) {
            try {
                const parsed = JSON.parse(stdout);
                latestCandidates = parsed.candidates || [];
                latestSelectedSchedule = parsed.selectedSchedule || [];
                writeSelectedSchedule(latestCandidates[0] || { rows: latestSelectedSchedule });
                return res.json({ ok: true, message: 'Scheduler completed', ...parsed });
            } catch (err) {
                return res.status(500).json({ ok: false, error: `Invalid scheduler output: ${err.message}` });
            }
        } else {
            return res.status(500).json({ ok: false, code, error: stderr || stdout });
        }
    });
});

app.post('/api/select-schedule', (req, res) => {
    const { candidateId } = req.body || {};
    const selected = latestCandidates.find((candidate) => candidate.id === candidateId);
    if (!selected) {
        return res.status(404).json({ error: 'Schedule candidate not found' });
    }

    writeSelectedSchedule(selected);
    return res.json({ ok: true, candidateId, rows: selected.rows || [] });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Backend running on http://localhost:${PORT}`));