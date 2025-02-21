
const bcrypt = require('bcrypt');
const User = require('../models/user');

const seedAdmin = async () => {
  try {
   
    const adminData = [
      {
        name: "admin",
        email: "mjchouhan456@gmail.com",
        password: "admin123",
        role: "admin"
      },
      {
        name: "admin",
        email: "mratyunjaychouhan45@gmail.com",
        password: "admin123",
        role: "admin"
      },
      {
        name: "admin",
        email: "mratyunjay3@gmail.com",
        password: "admin123",
        role: "admin"
      }
    ];

    for (const admin of adminData) {
      if (!admin.password) {
        console.error(`No password defined for admin with email ${admin.email}`);
        continue;
      }

      const existingAdmin = await User.findOne({ email: admin.email });
      if (existingAdmin) {
        console.log(`Admin user with email ${admin.email} already exists.`);
        continue;
      }

      const saltRounds = 10;
   
      console.log(`Hashing password for ${admin.email}`);
      admin.password = await bcrypt.hash(admin.password, saltRounds);

      const adminUser = new User(admin);
      await adminUser.save();
      console.log(`Admin user with email ${admin.email} created successfully.`);
    }
  } catch (error) {
    console.error("Error during admin seeding:", error.message);
  } 
};

seedAdmin();
