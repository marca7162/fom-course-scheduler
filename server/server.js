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
const csvDir = path.join(__dirname, '..', 'work', 'csv_files');
const candidatesFile = path.join(outputDir, 'schedule_candidates.json');
const uploadDir = path.join(__dirname, '..', 'work', 'uploads');
const bundledPython = path.join(__dirname, '..', '.venv', 'Scripts', 'python.exe');

function pythonExecutable() {
    if (process.env.PYTHON) return process.env.PYTHON;
    if (fs.existsSync(bundledPython)) return bundledPython;
    return 'python';
}

function runPython(scriptPath, args = []) {
    return new Promise((resolve, reject) => {
        const py = pythonExecutable();
        const proc = spawn(py, [scriptPath, ...args], {
            cwd: path.join(__dirname, '..'),
            stdio: ['ignore', 'pipe', 'pipe'],
        });
        let stdout = '';
        let stderr = '';
        proc.stdout.on('data', (data) => { stdout += data.toString(); });
        proc.stderr.on('data', (data) => { stderr += data.toString(); });
        proc.on('error', reject);
        proc.on('close', (code) => {
            if (code === 0) resolve(stdout);
            else reject(new Error(stderr.trim() || stdout.trim() || `Python exited with code ${code}`));
        });
    });
}

function loadSavedCandidates() {
    try {
        if (fs.existsSync(candidatesFile)) {
            const saved = JSON.parse(fs.readFileSync(candidatesFile, 'utf8'));
            latestCandidates = Array.isArray(saved) ? saved : [];
        }
    } catch (err) {
        console.warn(`Could not load saved schedule candidates: ${err.message}`);
        latestCandidates = [];
    }
}

function saveCandidates(candidates) {
    fs.mkdirSync(outputDir, { recursive: true });
    fs.writeFileSync(candidatesFile, JSON.stringify(candidates));
}

loadSavedCandidates();

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

function readCsvFile(filePath) {
    return new Promise((resolve, reject) => {
        const rows = [];
        fs.createReadStream(filePath)
            .pipe(csvParser())
            .on('data', (row) => rows.push(row))
            .on('end', () => resolve(rows))
            .on('error', reject);
    });
}

async function writeSelectedSchedule(candidate) {
    const courseRows = candidate.rows || [];
    const teacherRows = [];
    const studentRows = [];

    const [availability, enrollment] = await Promise.all([
        readCsvFile(path.join(csvDir, 'tokenized_availability.csv')),
        readCsvFile(path.join(csvDir, 'tokenized_enrollment.csv')),
    ]);
    const teacherByCourse = new Map(
        availability.map((row) => [row.course_id, row.teacher_name])
    );
    const studentsByCourse = new Map();
    enrollment.forEach((row) => {
        if (!studentsByCourse.has(row.course_id)) studentsByCourse.set(row.course_id, []);
        studentsByCourse.get(row.course_id).push(row.student_id);
    });

    courseRows.forEach((row) => {
        teacherRows.push({
            teacherName: teacherByCourse.get(row.courseCode) || 'Unknown',
            day: row.day,
            period: row.period,
            courseCode: row.courseCode,
            roomNumber: row.roomNumber,
        });
        (studentsByCourse.get(row.courseCode) || []).forEach((studentId) => {
            studentRows.push({
                studentId,
                courseCode: row.courseCode,
                day: row.day,
                period: row.period,
                roomNumber: row.roomNumber,
            });
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

app.post(
    '/api/upload-workbook',
    express.raw({ type: 'application/octet-stream', limit: '25mb' }),
    async (req, res) => {
        const originalName = decodeURIComponent(req.get('x-file-name') || 'schedule.xlsx');
        if (!originalName.toLowerCase().endsWith('.xlsx')) {
            return res.status(400).json({ ok: false, error: 'Please upload an .xlsx Excel workbook.' });
        }
        if (!Buffer.isBuffer(req.body) || req.body.length === 0) {
            return res.status(400).json({ ok: false, error: 'The uploaded workbook is empty.' });
        }
        // XLSX files are ZIP containers and begin with the PK signature.
        if (req.body[0] !== 0x50 || req.body[1] !== 0x4b) {
            return res.status(400).json({ ok: false, error: 'This file is not a valid .xlsx workbook.' });
        }

        fs.mkdirSync(uploadDir, { recursive: true });
        const safeName = `${Date.now()}-${path.basename(originalName).replace(/[^a-zA-Z0-9._-]/g, '_')}`;
        const uploadPath = path.join(uploadDir, safeName);
        fs.writeFileSync(uploadPath, req.body);

        try {
            const scriptPath = path.join(__dirname, '..', 'work', 'scripts', 'import_and_schedule.py');
            const stdout = await runPython(scriptPath, [uploadPath]);
            const jsonStart = stdout.indexOf('{"course_room"');
            const parsed = JSON.parse(jsonStart >= 0 ? stdout.slice(jsonStart) : stdout);
            latestCandidates = parsed.candidates || [];
            latestSelectedSchedule = parsed.selectedSchedule || [];
            saveCandidates(latestCandidates);
            await writeSelectedSchedule(latestCandidates[0] || { rows: latestSelectedSchedule });
            return res.json({
                ok: true,
                message: 'Workbook imported and schedules generated.',
                fileName: originalName,
                ...parsed,
            });
        } catch (err) {
            return res.status(422).json({
                ok: false,
                error: `Could not process workbook: ${err.message}`,
            });
        } finally {
            fs.rmSync(uploadPath, { force: true });
        }
    }
);

app.post('/api/run-scheduler', (req, res) => {
    const scriptPath = path.join(__dirname, '..', 'work', 'scripts', 'main.py');
    const py = pythonExecutable();
    const proc = spawn(py, [scriptPath, '--json'], { cwd: path.join(__dirname, '..'), stdio: ['ignore', 'pipe', 'pipe'] });

    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d.toString(); });
    proc.stderr.on('data', (d) => { stderr += d.toString(); });

    proc.on('close', async (code) => {
        if (code === 0) {
            try {
                const parsed = JSON.parse(stdout);
                latestCandidates = parsed.candidates || [];
                saveCandidates(latestCandidates);
                latestSelectedSchedule = parsed.selectedSchedule || [];
                await writeSelectedSchedule(latestCandidates[0] || { rows: latestSelectedSchedule });
                return res.json({ ok: true, message: 'Scheduler completed', ...parsed });
            } catch (err) {
                return res.status(500).json({ ok: false, error: `Invalid scheduler output: ${err.message}` });
            }
        } else {
            return res.status(500).json({ ok: false, code, error: stderr || stdout });
        }
    });
});

app.post('/api/select-schedule', async (req, res) => {
    const { candidateId } = req.body || {};
    const selected = latestCandidates.find((candidate) => candidate.id === candidateId);
    if (!selected) {
        return res.status(404).json({ error: 'Schedule candidate not found' });
    }

    await writeSelectedSchedule(selected);
    return res.json({ ok: true, candidateId, rows: selected.rows || [] });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Backend running on http://localhost:${PORT}`));
