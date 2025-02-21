require('dotenv').config();
const express = require('express');
const cors = require('cors');

const cookieParser = require('cookie-parser');
const app = express();
const userRoutes = require('./routes/user');
require('./config/dbConnect');
require('./controller/seedAdmin')

app.use(cors(
    {
        origin: "http://localhost:5173",
        credentials: true
    }
));
app.use(express.json());
app.use(cookieParser());

// Connect to MongoDB



// Use your API routes
app.use('/api', userRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
