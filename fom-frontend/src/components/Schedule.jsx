// frontend/src/components/Schedule.jsx
import { useState, useEffect, useCallback } from 'react';

const PERIOD_TIMES = {
    1: '9:30 – 10:50',
    2: '11:00 – 12:20',
    3: '12:30 – 13:50',
    4: '14:00 – 15:20',
    5: '15:30 – 16:50',
    6: '17:00 – 18:20',
    7: '18:30 – 19:50',
    8: '20:00 – 21:20',
};

const DAYS = ['M', 'T', 'W', 'TH', 'F'];

function Schedule() {
    const [scheduleData, setScheduleData] = useState([]);
    const [loading, setLoading] = useState(true);   // start as true
    const [error, setError] = useState(null);
    const [schedulerRunning, setSchedulerRunning] = useState(false);
    const [schedulerMessage, setSchedulerMessage] = useState('');

    // Fetch schedule data – does NOT set loading(true)
    const fetchSchedule = useCallback(() => {
        fetch('/api/course-schedule')
            .then(res => {
                if (!res.ok) throw new Error('Network response was not ok');
                return res.json();
            })
            .then(data => {
                setScheduleData(data);
                setLoading(false);   // set false on success
            })
            .catch(err => {
                setError(err.message);
                setLoading(false);   // set false on error too
            });
    }, []);

    // Run once on mount – no synchronous setState inside
    useEffect(() => {
        fetchSchedule();
    }, [fetchSchedule]);

    const runScheduler = () => {
        setSchedulerRunning(true);
        setSchedulerMessage('Running scheduler...');
        setError(null);

        fetch('/api/run-scheduler', { method: 'POST' })
            .then(res => {
                if (!res.ok) throw new Error('Scheduler failed');
                return res.json();
            })
            .then(() => {
                setSchedulerMessage('Scheduler completed successfully!');
                // Refresh schedule – will set loading(false) when done
                setLoading(true);   // optionally show loading again
                fetchSchedule();
            })
            .catch(err => {
                setError(err.message);
                setSchedulerMessage('Scheduler failed.');
            })
            .finally(() => {
                setSchedulerRunning(false);
            });
    };

    if (loading) return <div className="text-center mt-5">Loading schedule...</div>;
    if (error) return <div className="alert alert-danger">Error: {error}</div>;

    // Build lookup
    const lookup = {};
    scheduleData.forEach(row => {
        const day = row.day;
        const period = parseInt(row.period, 10);
        if (!lookup[day]) lookup[day] = {};
        lookup[day][period] = { course: row.courseCode, room: row.roomNumber };
    });

    const periods = [...new Set(scheduleData.map(r => parseInt(r.period, 10)))].sort((a, b) => a - b);

    return (
        <div className="container-fluid mt-4" style={{ paddingTop: '80px' }}>
            <h2 className="mb-3">Course Schedule</h2>
            <div className="table-responsive">
                <table className="table table-bordered table-striped text-center">
                    <thead>
                    <tr>
                        <th>Days</th>
                        {periods.map(p => (
                            <th key={p}>
                                <div>Period {p}</div>
                                <small>{PERIOD_TIMES[p] || p}</small>
                            </th>
                        ))}
                    </tr>
                    </thead>
                    <tbody>
                    {/*Passing the data from the get results to the cards*/}
                    {DAYS.map(day => (
                        <tr key={day}>
                            <td className="fw-bold">{day}</td>
                            {periods.map(p => {
                                const cell = lookup[day]?.[p];
                                return (
                                    <td key={`${day}-${p}`}>
                                        {cell ? (
                                            <div className="card bg-light border-primary" style={{ padding: '8px' }}>
                                                <div className="card-body p-1">
                                                    <h6 className="card-title mb-0">{cell.course}</h6>
                                                    <p className="card-text mb-0 small">Room: {cell.room}</p>
                                                </div>
                                            </div>
                                        ) : (
                                            <span className="text-muted">—</span>
                                        )}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>
            <p className="text-muted small mt-2">Only periods with scheduled courses are shown.</p>

            <div className="text-center mt-4">
                <button
                    className="btn btn-primary"
                    onClick={runScheduler}
                    disabled={schedulerRunning}
                >
                    {schedulerRunning ? 'Running...' : 'Run Scheduler'}
                </button>
                {schedulerMessage && (
                    <div className="mt-2 text-muted">{schedulerMessage}</div>
                )}
            </div>
        </div>
    );
}

export default Schedule;