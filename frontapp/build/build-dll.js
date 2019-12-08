const path = require("path");
const webpack = require("webpack");
const dllConfig = require("./webpack.dll.conf");
const chalk = require("chalk");
const rm = require("rimraf");
const ora = require("ora");

const spinner = ora({
  color: "green",
  text: "building for Dll..."
});
spinner.start();
rm(path.resolve(__dirname, "../libs"), err => {
  if (err) throw err;
  webpack(dllConfig, function(err, stats) {
    spinner.stop();
    if (err) throw err;
    process.stdout.write(
      stats.toString({
        colors: true,
        modules: false,
        children: false,
        chunks: false,
        chunkModules: false
      }) + "\n\n"
    );
    console.log(chalk.cyan(" build dll succeed !.\n"));
  });
});
