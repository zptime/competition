/**
 * 验证版本
 */
'use strict'
//chalk是一个颜色插件。
const chalk = require('chalk')
//semver一个版本控制插件
const semver = require('semver')
const packageConfig = require('../package.json')
//shelljss是nodejs对与多进程的支持，是对于child_process封装
const shell = require('shelljs')

function exec (cmd) {
  return require('child_process').execSync(cmd).toString().trim()
}

const versionRequirements = [
  {//对应node的版本
    name: 'node',
    //当前环境版本，semver.clean把当前环境版本信息转化规定格式，也是'  =v1.2.3  '->'1.2.3'
    currentVersion: semver.clean(process.version),
    //要求版本，对应package.json的engines所配置的信息
    versionRequirement: packageConfig.engines.node
  }
]

//npm环境中
if (shell.which('npm')) {
  versionRequirements.push({
    name: 'npm',
    //执行方法得到版本号
    currentVersion: exec('npm --version'),
    versionRequirement: packageConfig.engines.npm
  })
}

module.exports = function () {
  const warnings = []

  for (let i = 0; i < versionRequirements.length; i++) {
    const mod = versionRequirements[i]

    //如果版本号不符合package.json文件中指定的版本号，就执行下面的代码
    if (!semver.satisfies(mod.currentVersion, mod.versionRequirement)) {
      warnings.push(mod.name + ': ' +
        chalk.red(mod.currentVersion) + ' should be ' +
        chalk.green(mod.versionRequirement)
      )
    }
  }

  if (warnings.length) {
    console.log('')
    console.log(chalk.yellow('To use this template, you must update following to modules:'))
    console.log()

    for (let i = 0; i < warnings.length; i++) {
      const warning = warnings[i]
      console.log('  ' + warning)
    }

    console.log()
    process.exit(1)
  }
}
