#ifndef COMPILER_UTILS_HH
#define COMPILER_UTILS_HH

#include <clang/AST/ASTConsumer.h>
#include <clang/AST/RecursiveASTVisitor.h>
#include <clang/Basic/Diagnostic.h>
#include <clang/Basic/FileManager.h>
#include <clang/Basic/SourceManager.h>
#include <clang/Basic/TargetInfo.h>
#include <clang/Basic/TargetOptions.h>
#include <clang/Frontend/CompilerInstance.h>
#include <clang/Frontend/FrontendAction.h>
#include <clang/Lex/Preprocessor.h>
#include <clang/Parse/ParseAST.h>
#include <clang/Rewrite/Core/Rewriter.h>
#include <clang/Rewrite/Frontend/Rewriters.h>
#include <clang/Tooling/Tooling.h>
#include <llvm/Support/Host.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/Support/FileSystem.h>
#include "consumer.hh"
#include <nlohmann/json.hpp>
#include <fstream> 


using namespace clang;
using namespace std;

void consumeAST(CompilerInstance &CI, MyConsumer &consumer);

void createCompilerInstance(CompilerInstance &theCompiler,
                            const string &filename);

Rewriter createRewriter(CompilerInstance &CI);

bool writeRewriterOutputToFile(Rewriter& rewriter, const string &filename);


void writeJSONToFile(const nlohmann::json &j, const string &filename);

#endif