const express = require('express');
const router = express.Router();
const { Register, SignIn } = require("../controller/userAuth");



router.post('/register', Register);
router.post('/signin', SignIn);




module.exports = router;
