'use strict'
const path = require('path')
const utils = require('./utils')
const webpack = require('webpack')
const config = require('../config')
const merge = require('webpack-merge')
const baseWebpackConfig = require('./webpack.base.conf')
const CopyWebpackPlugin = require('copy-webpack-plugin')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const ExtractTextPlugin = require('extract-text-webpack-plugin')
const OptimizeCSSPlugin = require('optimize-css-assets-webpack-plugin')
const UglifyJsPlugin = require('uglifyjs-webpack-plugin')
// const bundleConfig = require("../static/libs/bundle-config.json")
// const ParallelUglifyPlugin = require('webpack-parallel-uglify-plugin')


const env = require('../config/prod.env')

const webpackConfig = merge(baseWebpackConfig, {
  module: {
    rules: utils.styleLoaders({
      sourceMap: config.build.productionSourceMap,
      extract: true,
      usePostCSS: true
    })
  },
  devtool: config.build.productionSourceMap ? config.build.devtool : false,
  output: {
    path: config.build.assetsRoot,
    filename: utils.assetsPath('js/[name].[chunkhash].js'),//浏览器缓存，增加hash值
    chunkFilename: utils.assetsPath('js/[id].[chunkhash].js')
  },
  plugins: [
    //增加DllReferencePlugin配置
    new webpack.DllReferencePlugin({
      context: __dirname,
      manifest: require("../static/libs/vendor-mainfest.json") // 指向生成的manifest.json
    }),
    // http://vuejs.github.io/vue-loader/en/workflow/production.html
    new webpack.DefinePlugin({
      'process.env': env
    }),
    new UglifyJsPlugin({
      uglifyOptions: {
        compress: {
          warnings: false
        }
      },
      sourceMap: config.build.productionSourceMap,
      parallel: true
    }),
    //增加 webpack-parallel-uglify-plugin来替换
    // new ParallelUglifyPlugin({
    //   cacheDir: '.cache/',
    //   uglifyJS: {
    //     output: {
    //       beautify: false,
    //       comments: false
    //     },
    //     compress: {
    //       warnings: false,
    //       drop_console: true,
    //       collapse_vars: true,
    //       reduce_vars: true
    //     }
    //   }
    // }),
    // extract css into its own file
    new ExtractTextPlugin({
      filename: utils.assetsPath('css/[name].[contenthash].css'),
      // Setting the following option to `false` will not extract CSS from codesplit chunks.
      // Their CSS will instead be inserted dynamically with style-loader when the codesplit chunk has been loaded by webpack.
      // It's currently set to `true` because we are seeing that sourcemaps are included in the codesplit bundle as well when it's `false`,
      // increasing file size: https://github.com/vuejs-templates/webpack/issues/1110
      allChunks: true,
    }),
    // Compress extracted CSS. We are using this plugin so that possible
    // duplicated CSS from different components can be deduped.
    new OptimizeCSSPlugin({
      cssProcessorOptions: config.build.productionSourceMap
        ? { safe: true, map: { inline: false } }
        : { safe: true }
    }),
    // generate dist index.html with correct asset hash for caching.
    // you can customize output by editing /index.html
    // see https://github.com/ampedandwired/html-webpack-plugin
    //生成html index.html → app.js
    new HtmlWebpackPlugin({
      filename: config.build.index,//生成的html
      template: 'index.html',//来源html
      //js资源插入位置,true表示插入到body元素底部
      inject: true,
      minify: {//压缩配置
        removeComments: true,//删除Html注释
        collapseWhitespace: true,//去除空格
        removeAttributeQuotes: true //去除属性引号
        // more options:
        // https://github.com/kangax/html-minifier#options-quick-reference
      },
      // 增加两个变量
      // libJsName: bundleConfig.libs.js,
      // libCssName: bundleConfig.libs.css,
      // necessary to consistently work with multiple chunks via CommonsChunkPlugin
      chunksSortMode: 'dependency' //根据依赖引入chunk
    }),
    // keep module.id stable when vendor modules does not change
    //webpack里每个模块都有一个 module id ，module id 是该模块在模块依赖关系图里按顺序分配的序号，如果这个 module id 发生了变化，那么它的 chunkhash 也会发生变化。
    //这样会导致：如果你引入一个新的模块，会导致 module id 整体发生改变，可能会导致所有文件的chunkhash发生变化。
    //这里需要用 HashedModuleIdsPlugin ，根据模块的相对路径生成一个四位数的hash作为模块id，这样就算引入了新的模块，也不会影响 module id 的值，只要模块的路径不改变的话。
    new webpack.HashedModuleIdsPlugin(),
    // enable scope hoisting //“作用域提升”,打包出来的代码文件更小、运行的更快
    new webpack.optimize.ModuleConcatenationPlugin(),
    // split vendor js into its own file
    // 1. 第三方库chunk：把node_modules下面以 .js 结尾的，并且不是重复的模块提取到vender里面。打包后会生成app.js(业务代码)、vender.js(框架代码)这两个文件
    new webpack.optimize.CommonsChunkPlugin({
      name: 'vendor',
      minChunks (module) {
        // any required modules inside node_modules are extracted to vendor
        // 在node_modules的js文件!
        return (
          module.resource &&
          /\.js$/.test(module.resource) &&
          module.resource.indexOf(
            path.join(__dirname, '../node_modules')
          ) === 0
        )
      }
    }),
    // extract webpack runtime and module manifest to its own file in order to
    // prevent vendor hash from being updated whenever app bundle is updated
    // 2. 缓存chunk，提取manifast文件的原因：vendor chunk 里面包含了 webpack 的 runtime 代码（用来解析和加载模块之类的运行时代码）
    //这样会导致：即使你没有更改引入模块(vendor的模块没有发生变动的情况下，你仅仅修改了其他代码) 也会导致 vendor 的chunkhash值发生变化，从而破坏了缓存，达不到预期效果
    new webpack.optimize.CommonsChunkPlugin({
      name: 'manifest',
      minChunks: Infinity
    }),
    // This instance extracts shared chunks from code splitted chunks and bundles them
    // in a separate chunk, similar to the vendor chunk
    // see: https://webpack.js.org/plugins/commons-chunk-plugin/#extra-async-commons-chunk
    // 3.异步 公共chunk
    new webpack.optimize.CommonsChunkPlugin({
      name: 'app',
      async: 'vendor-async',// (创建一个异步 公共chunk)
      children: true,// (选择所有被选 chunks 的子 chunks)
      minChunks: 3 // (在提取之前需要至少三个子 chunk 共享这个模块)
    }),

    // copy custom static assets
    //将整个文件复制到构建输出指定目录下
    new CopyWebpackPlugin([
      {
        from: path.resolve(__dirname, '../static'),
        to: config.build.assetsSubDirectory,
        ignore: ['.*']
      },
      // {// 增加一个静态文件目录
      //   from: path.resolve(__dirname, "../libs"),
      //   to: config.build.assetsSubDirectory,
      //   ignore: ["*.json"]
      // }
    ])
  ]
})

if (config.build.productionGzip) {
  const CompressionWebpackPlugin = require('compression-webpack-plugin')

  webpackConfig.plugins.push(
    new CompressionWebpackPlugin({
      asset: '[path].gz[query]',
      algorithm: 'gzip',
      test: new RegExp(
        '\\.(' +
        config.build.productionGzipExtensions.join('|') +
        ')$'
      ),
      threshold: 10240,
      minRatio: 0.8
    })
  )
}

if (config.build.bundleAnalyzerReport) {//配置是否开启webpack文件分析
  const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin
  webpackConfig.plugins.push(new BundleAnalyzerPlugin())
}

module.exports = webpackConfig
