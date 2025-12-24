// index.js
// import express from 'express';
// import mongoose from 'mongoose';
// import cors from 'cors';
// import dotenv from 'dotenv';
// import policeRoutes from './routes/police.js';
// import reportRoutes from './routes/missingReport.js';
// import userRoutes from './routes/user.js';

// dotenv.config();

// const app = express();

import express from 'express';
import path from 'path';
import fs from 'fs';
import mongoose from 'mongoose';
import cors from 'cors';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url'; // <-- add this import
import policeRoutes from './routes/police.js';
import reportRoutes from './routes/missingReport.js';
import userRoutes from './routes/user.js';

import reportsRouter from './routes/missingReport.js';

import alertsRouter from './routes/alerts.js';
import { startRtspToHls } from './streaming/rtspToHls.js';


dotenv.config();

const app = express();

// Fix __dirname for ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);


// Middleware
const allowedOrigins = [
    "https://project-1ndc.onrender.com",
    "https://group9.telvexsolutions.co.in",
    "http://localhost:5173"
];

app.use(cors({
    origin: function (origin, callback) {
        // Allow requests with no origin (like mobile apps, Postman)
        if (!origin) return callback(null, true);

        if (allowedOrigins.includes(origin)) {
            return callback(null, true);
        } else {
            return callback(new Error("Not allowed by CORS"));
        }
    },
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allowedHeaders: ["Content-Type", "Authorization"],
    credentials: true
}));
app.use(express.json());
// app.use('/uploads', express.static('uploads')); // for uploaded images
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));


// Simple homepage route
app.get('/', (req, res) => {
  res.send('Backend is running ✅');
});

// API Routes

app.use('/api', alertsRouter);

app.use('/api/reports', reportsRouter);

app.use('/api/police', policeRoutes);
app.use('/api/reports', reportRoutes);
app.use('/api/users', userRoutes);

// HLS streaming for RTSP cameras
const streamsRoot = path.join(__dirname, 'streams');
if (!fs.existsSync(streamsRoot)) {
  fs.mkdirSync(streamsRoot, { recursive: true });
}
app.use('/hls', express.static(streamsRoot));

// Start RTSP -> HLS for "people" camera
const rtspPeopleUrl = process.env.RTSP_PEOPLE_URL || 'rtsp://rtspstream:RtxI20Zn-D4alMBGdfYjO@zephyr.rtsp.stream/people';
startRtspToHls('people', rtspPeopleUrl, streamsRoot);

// MongoDB Connection
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('MongoDB connected'))
  .catch(err => console.log('MongoDB connection error:', err));

// Start server
const PORT = process.env.PORT || 5050;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
