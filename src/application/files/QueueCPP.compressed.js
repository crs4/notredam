/* QueueCPP.js - a function for creating an efficient queue in JavaScript
 *
 * The author of this program, Safalra (Stephen Morley), irrevocably releases
 * all rights to this program, with the intention of it becoming part of the
 * public domain. Because this program is released into the public domain, it
 * comes with no warranty either expressed or implied, to the extent permitted
 * by law.
 *
 * For more public domain JavaScript code by the same author, visit:
 *
 * http://www.safalra.com/web-design/javascript/
 */

function Queue(){var _1=[];var _2=0;this.size=function(){return _1.length-_2;};this.empty=function(){return (_1.length==0);};this.push=function(_3){_1.push(_3);};this.pop=function(){var _4=undefined;if(_1.length){_4=_1[_2];if(++_2*2>=_1.length){_1=_1.slice(_2);_2=0;}}return _4;};this.front=function(){var _5=undefined;if(_1.length){_5=_1[_2];}return _5;};}
