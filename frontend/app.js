const express = require('express');
const axios = require('axios');
const path = require('path');

const app = express();
const API_URL = process.env.API_URL || "http://api:8000";

app.use(express.json());
app.use(express.static(path.join(__dirname, 'views')));


app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

app.post('/submit', async (req, res) => {
  try {
    const response = await axios.post(`${API_URL}/jobs`, req.body);
    res.json(response.data);
  } catch (err) {
    console.error(err?.response?.data || err.message);
    res.status(500).json({ error: "something went wrong" });
  }
});

app.get('/status/:id', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/jobs/${req.params.id}`);
    res.json(response.data);
  } catch (err) {
    console.error(err?.response?.data || err.message);
    res.status(500).json({ error: "something went wrong" });
  }
});

app.listen(3000, '0.0.0.0', () => {
  console.log('Frontend running on port 3000');
});