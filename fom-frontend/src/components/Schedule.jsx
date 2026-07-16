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
};

const DAYS = ['M', 'T', 'W', 'TH'];

function Schedule() {
    const [scheduleData, setScheduleData] = useState([]);
    const [appliedScheduleData, setAppliedScheduleData] = useState([]);
    const [scheduleCandidates, setScheduleCandidates] = useState([]);
    const [selectedCandidateId, setSelectedCandidateId] = useState('');
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
        setLoading(true);

        fetch('/api/run-scheduler', { method: 'POST' })
            .then(res => {
                if (!res.ok) throw new Error('Scheduler failed');
                return res.json();
            })
            .then((data) => {
                if (data?.selectedSchedule) {
                    setScheduleData(data.selectedSchedule);
                    setAppliedScheduleData(data.selectedSchedule);
                }
                if (data?.candidates) {
                    // show at most three candidate schedules
                    setScheduleCandidates(data.candidates.slice(0, 3));
                    setSelectedCandidateId(data.selectedCandidateId || '');
                    if (data.selectedCandidateId) {
                        // persist server-selected candidate id
                        try { localStorage.setItem('selectedScheduleId', data.selectedCandidateId); } catch (e) { }
                    }
                }
                setSchedulerMessage('Scheduler completed successfully!');
                // refresh the canonical schedule from server if available
                fetchSchedule();
            })
            .catch(err => {
                setError(err.message);
                setSchedulerMessage('Scheduler failed.');
            })
            .finally(() => {
                setSchedulerRunning(false);
                setLoading(false);
            });
    };

    // preview selection before applying as baseline
    const [previewCandidateId, setPreviewCandidateId] = useState('');

    const applyPreviewAsBaseline = () => {
        if (!previewCandidateId) return;
        chooseCandidate(previewCandidateId);
    };

    const chooseCandidate = (candidateId) => {
        fetch('/api/select-schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ candidateId }),
        })
            .then(async res => {
                if (!res.ok) {
                    if (res.status === 404) {
                        try { localStorage.removeItem('selectedScheduleId'); } catch (e) { }
                        throw new Error('That saved schedule is no longer available. Run the scheduler again.');
                    }
                    const body = await res.json().catch(() => ({}));
                    throw new Error(body.error || 'Could not apply schedule choice');
                }
                return res.json();
            })
            .then((data) => {
                setSelectedCandidateId(candidateId);
                setPreviewCandidateId(candidateId);
                setScheduleData(data.rows || []);
                setAppliedScheduleData(data.rows || []);
                // persist selection for the rest of the app
                try { localStorage.setItem('selectedScheduleId', candidateId); } catch (e) { }
                // notify other parts of app
                try { window.dispatchEvent(new CustomEvent('scheduleChanged', { detail: { selectedCandidateId: candidateId } })); } catch (e) { }
                setSchedulerMessage('Selected schedule has been applied.');
            })
            .catch((err) => {
                setError(err.message);
            });
    };

    // initialize selected candidate from localStorage (apply on mount)
    useEffect(() => {
        try {
            const saved = localStorage.getItem('selectedScheduleId');
            if (saved) {
                // attempt to apply saved selection from server
                chooseCandidate(saved);
            }
        } catch (e) { }
    }, []);

    // when preview changes, show candidate rows but don't overwrite appliedScheduleData
    useEffect(() => {
        if (!previewCandidateId) {
            // revert to applied schedule
            setScheduleData(appliedScheduleData || []);
            return;
        }
        const cand = scheduleCandidates.find(c => c.id === previewCandidateId);
        if (cand) {
            setScheduleData(cand.rows || []);
        }
    }, [previewCandidateId, scheduleCandidates, appliedScheduleData]);

    if (loading) return <div className="text-center mt-5">Loading schedule...</div>;
    if (error) return <div className="alert alert-danger">Error: {error}</div>;

    // Build lookup for day/period so we can show multiple courses if they overlap
    const lookup = {};
    scheduleData.forEach(row => {
        const day = row.day;
        const period = parseInt(row.period, 10);
        if (!lookup[day]) lookup[day] = {};
        if (!lookup[day][period]) lookup[day][period] = [];
        lookup[day][period].push({ course: row.courseCode, room: row.roomNumber });
    });

    const periods = [
        ...new Set(scheduleData.map(r => parseInt(r.period, 10)))
    ].sort((a, b) => a - b).filter(p => p !== 8);

    const courseColors = new Map(
        [...new Set(scheduleData.map(row => row.courseCode))]
            .sort()
            .map((courseCode, index) => {
                const hue = Math.round((index * 137.508) % 360);
                return [courseCode, {
                    backgroundColor: `hsl(${hue} 72% 90%)`,
                    borderColor: `hsl(${hue} 58% 48%)`,
                    color: `hsl(${hue} 45% 20%)`,
                }];
            })
    );

    return (
        <div className="container-fluid mt-4" style={{ paddingTop: '80px' }}>
            <h2 className="mb-3">Course Schedule</h2>
            <div className="table-responsive">
                <table className="table table-bordered text-center schedule-table">
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
                                const cell = lookup[day]?.[p] || [];
                                const roomGroups = cell.reduce((groups, entry) => {
                                    if (!groups[entry.room]) groups[entry.room] = [];
                                    groups[entry.room].push(entry);
                                    return groups;
                                }, {});
                                const hasConflict = Object.values(roomGroups).some(group => group.length > 1);
                                return (
                                    <td key={`${day}-${p}`} style={{ verticalAlign: 'top' }}>
                                        {cell.length > 0 ? (
                                            /* 1. Flex container to hold our individual "sub-cells" side-by-side */
                                            <div className="d-flex flex-column gap-2 h-100 align-items-stretch">
                                                {cell.map((entry, index) => {
                                                    
                                                    /* 2. Check conflict per-entry: Does another class in this cell share this room? */
                                                    const isConflictingEntry = cell.some(
                                                        (other, otherIdx) => other.room === entry.room && otherIdx !== index
                                                    );

                                                    return (
                                                        /* 3. Each class now gets its own independent, flexible card */
                                                        <div
                                                            key={`${entry.course}-${entry.room}-${index}`}
                                                            className={`card flex-fill course-block ${isConflictingEntry ? 'course-block-conflict' : ''}`}
                                                            style={courseColors.get(entry.course)}
                                                        >
                                                            {isConflictingEntry && (
                                                                <div className="small text-danger fw-bold mb-1">Room Conflict</div>
                                                            )}
                                                            <div className="card-body p-1">
                                                                <h6 className="card-title mb-0">{entry.course}</h6>
                                                                <p className="card-text mb-0 small">Room: {entry.room}</p>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
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
            {scheduleCandidates.length > 0 && (
                <div className="mt-4">
                    <h4 className="h5">Schedule options</h4>
                    <p className="text-muted small">Choose the option with the fewest conflicts to work with.</p>
                    <div className="row gy-3">
                        {scheduleCandidates.map((candidate) => {
                            const isSelected = selectedCandidateId === candidate.id;
                            return (
                                <div className="col-md-4" key={candidate.id}>
                                    <div className={`card h-100 ${isSelected ? 'border-primary shadow-sm' : 'border-light'}`}>
                                        <div className="card-body">
                                            <div className="form-check form-check-inline mb-2">
                                                <input
                                                    className="form-check-input"
                                                    type="radio"
                                                    name="candidatePreview"
                                                    id={`preview-${candidate.id}`}
                                                    checked={previewCandidateId === candidate.id}
                                                    onChange={() => {
                                                        setPreviewCandidateId(candidate.id);
                                                        chooseCandidate(candidate.id);
                                                    }}
                                                />
                                                <label className="form-check-label small" htmlFor={`preview-${candidate.id}`}>
                                                    Choose this schedule
                                                </label>
                                            </div>
                                            <h5 className="card-title">{candidate.name}</h5>
                                            <p className="card-text mb-2">
                                                <strong>{candidate.conflictCount}</strong> student conflicts
                                            </p>
                                            <p className="card-text small text-muted">
                                                {candidate.rows.length} course meetings
                                            </p>
                                            <button
                                                className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline-primary'}`}
                                                onClick={() => chooseCandidate(candidate.id)}
                                            >
                                                {isSelected ? 'Selected' : 'Use this schedule'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                    {/** Apply preview as baseline button */}
                    <div className="mt-3">
                        <button
                            className="btn btn-secondary btn-sm"
                            onClick={applyPreviewAsBaseline}
                            disabled={!previewCandidateId || previewCandidateId === selectedCandidateId}
                        >
                            Apply selected as baseline
                        </button>
                    </div>
                </div>
            )}

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
