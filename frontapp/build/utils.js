/**
 * webpack开发环境：主要用来处理css-loader和vue-style-loader
 */
'use strict'
const path = require('path')
const config = require('../config')
//引入extract-text-webpack-plugin插件，用来将css提取到单独的css文件中
const ExtractTextPlugin = require('extract-text-webpack-plugin')
const packageConfig = require('../package.json')

exports.assetsPath = function (_path) {
  //process.env.NODE_ENV在bulid.js中定义
  //如果为生产环境assetsSubDirectory为“static”，否则也为“static”
  //config.build.assetsSubDirectory与config.dev.assetsSubDirectory都在config/index中定义
  const assetsSubDirectory = process.env.NODE_ENV === 'production'
    ? config.build.assetsSubDirectory
    : config.dev.assetsSubDirectory

  //path.join和path.posix.join区别前者返回完整路径，后者返回完整路径的相对路径
  //例：path.join是E:/shishans/blogsss/static，path.posix.join是static
  return path.posix.join(assetsSubDirectory, _path)
}

exports.cssLoaders = function (options) {
  options = options || {}

  //css-loader的基本配置
  const cssLoader = {
    loader: 'css-loader',
    options: {
      //option用于配置loder的
      //是否开启cssMap，默认是false
      //一般我们会压缩js或者css以节省宽带,但在开发压缩就很难调试
      //所以用sourceMap进行关联，给出对应的sourceMap文件
      sourceMap: options.sourceMap,
      minimize:true
    }
  }

  const postcssLoader = {
    loader: 'postcss-loader',
    options: {
      sourceMap: options.sourceMap
    }
  }

  // generate loader string to be used with extract text plugin
  function generateLoaders (loader, loaderOptions) {
    //将上面的基础配置放到一个数据中
    const loaders = options.usePostCSS ? [cssLoader, postcssLoader] : [cssLoader]
    //如果该函数传递了单独的loder就加入到loaders数组中例如：sass或者less之类的
    if (loader) {
      loaders.push({
        //加载对应的loader
        loader: loader + '-loader',
        //es6方法Object.assign：主要用于合并对象的，浅拷贝
        options: Object.assign({}, loaderOptions, {
          sourceMap: options.sourceMap
        })
      })
    }

    // Extract CSS when that option is specified
    // (which is the case during production build)
    // extract自定义属性，用ExtractTextPlugin.extract控制是否把文件单独提取
    // true：单独提取，false表示不提取
    if (options.extract) {
      return ExtractTextPlugin.extract({
        use: loaders,
        fallback: 'vue-style-loader'
      })
    } else {
      //[].concat()方法用于连接数组
      return ['vue-style-loader'].concat(loaders)
    }
  }

  // https://vue-loader.vuejs.org/en/configurations/extract-css.html
  return {
    css: generateLoaders(),//返回[cssLoader, vue-style-loader]
    postcss: generateLoaders(),//返回[cssLoader, vue-style-loader]
    less: generateLoaders('less'),//返回[cssLoader, vue-style-loader, less]
    sass: generateLoaders('sass', { indentedSyntax: true }),
    scss: generateLoaders('sass'),
    stylus: generateLoaders('stylus'),
    styl: generateLoaders('stylus')
  }
}

// Generate loaders for standalone style files (outside of .vue)
// 这个方法主要处理import这种方式导入的文件类型的打包
exports.styleLoaders = function (options) {
  const output = []
  const loaders = exports.cssLoaders(options)

  for (const extension in loaders) {
    const loader = loaders[extension]
    output.push({
      test: new RegExp('\\.' + extension + '$'),
      use: loader
    })
  }

  return output
}

//用于返回脚手架错误的函数
exports.createNotifierCallback = () => {
  //使用node-notifier来发送桌面消息,包括应用状态改变以及错误信息
  const notifier = require('node-notifier')

  return (severity, errors) => {
    if (severity !== 'error') return

    const error = errors[0]
    const filename = error.file && error.file.split('!').pop()

    notifier.notify({
      title: packageConfig.name,
      message: severity + ': ' + error.name,
      subtitle: filename || '',
      icon: path.join(__dirname, 'logo.png')
    })
  }
}
