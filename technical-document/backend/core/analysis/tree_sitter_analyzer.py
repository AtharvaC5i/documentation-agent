import os
import json
from typing import List

from core.analysis.analysis_models import AnalysisResult
from core.analysis.tech_stack_detector import detect_tech_stack


# ── Extension → display language ─────────────────────────────────────────
EXTENSION_TO_LANGUAGE = {
    ".py": "Python", ".pyw": "Python", ".pyx": "Python", ".wsgi": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "CSS", ".sass": "CSS", ".less": "CSS",
    ".vue": "Vue", ".svelte": "Svelte",
    ".java": "Java",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".groovy": "Groovy", ".scala": "Scala",
    ".clj": "Clojure", ".cljs": "Clojure",
    ".cs": "C#", ".vb": "VB.NET", ".fs": "F#", ".fsx": "F#", ".razor": "C#",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++",
    ".rs": "Rust", ".go": "Go", ".zig": "Zig",
    ".swift": "Swift", ".m": "Objective-C", ".dart": "Dart",
    ".rb": "Ruby", ".rake": "Ruby", ".gemspec": "Ruby", ".erb": "Ruby",
    ".php": "PHP", ".phtml": "PHP",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".fish": "Shell",
    ".ps1": "PowerShell", ".psm1": "PowerShell",
    ".bat": "Batch", ".cmd": "Batch",
    ".sql": "SQL",
    ".r": "R", ".rmd": "R",
    ".jl": "Julia",
    ".tf": "Terraform", ".tfvars": "Terraform",
    ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML", ".json": "JSON",
    ".j2": "Jinja2", ".jinja": "Jinja2",
    ".hbs": "Handlebars", ".ejs": "EJS",
    ".ex": "Elixir", ".exs": "Elixir",
    ".erl": "Erlang", ".hrl": "Erlang",
    ".hs": "Haskell", ".lhs": "Haskell",
    ".lua": "Lua",
    ".pl": "Perl", ".pm": "Perl",
    ".ml": "OCaml", ".mli": "OCaml",
    ".nim": "Nim", ".cr": "Crystal",
    ".sol": "Solidity",
    ".proto": "Protobuf",
    ".graphql": "GraphQL", ".gql": "GraphQL",
}

SOURCE_EXTENSIONS = {
    ".py", ".pyw", ".pyx",
    ".js", ".mjs", ".cjs", ".jsx",
    ".ts", ".tsx", ".mts",
    ".vue", ".svelte",
    ".java", ".kt", ".kts", ".groovy", ".scala",
    ".cs", ".vb", ".fs", ".fsx",
    ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp",
    ".rs", ".go", ".zig",
    ".swift", ".m", ".dart",
    ".rb", ".rake",
    ".php", ".phtml",
    ".sh", ".bash", ".ps1",
    ".r", ".jl",
    ".ex", ".exs", ".erl",
    ".hs", ".lua", ".pl", ".sol",
}

# ── Framework signatures (content-based) ─────────────────────────────────
FRAMEWORK_SIGNATURES = {
    # Python web
    "fastapi":       ["fastapi", "APIRouter(", "FastAPI(", "from fastapi"],
    "django":        ["from django", "django.db", "DJANGO_SETTINGS",
                      "django.contrib", "models.Model"],
    "flask":         ["from flask", "Flask(__name__)", "@app.route",
                      "flask import", "Blueprint(", "flask_restful"],
    "tornado":       ["import tornado", "tornado.web", "tornado.ioloop"],
    "aiohttp":       ["import aiohttp", "aiohttp.web", "web.Application()"],
    "starlette":     ["from starlette", "starlette.applications"],
    "litestar":      ["from litestar", "Litestar("],
    "sanic":         ["from sanic", "Sanic("],
    # Python ML/AI
    "tensorflow":    ["import tensorflow", "from tensorflow", "tf.keras"],
    "pytorch":       ["import torch", "from torch", "torch.nn"],
    "sklearn":       ["from sklearn", "import sklearn"],
    "pandas":        ["import pandas", "from pandas", "pd.DataFrame"],
    "numpy":         ["import numpy", "import numpy as np"],
    "langchain":     ["from langchain", "import langchain"],
    "langgraph":     ["from langgraph", "import langgraph"],
    "openai":        ["from openai", "import openai", "openai.ChatCompletion",
                      "OpenAI("],
    "huggingface":   ["from transformers", "from datasets", "AutoModel"],
    "celery":        ["from celery", "import celery", "Celery("],
    # JavaScript / Node
    "express":       ["require('express')", 'require("express")',
                      "express()", "Router()", "app.listen("],
    "nextjs":        ["from 'next'", 'from "next"', "getServerSideProps",
                      "getStaticProps", "next/router", "NextPage"],
    "nuxtjs":        ["defineNuxtConfig", "useNuxtApp", "from 'nuxt'"],
    "react":         ["from 'react'", 'from "react"', "React.Component",
                      "useState(", "useEffect(", "useContext(",
                      "ReactDOM.render", "createRoot("],
    "vue":           ["from 'vue'", 'from "vue"', "createApp(",
                      "defineComponent(", "ref(", "reactive("],
    "angular":       ["@NgModule", "@Component", "@Injectable",
                      "from '@angular/", "platformBrowserDynamic"],
    "svelte":        ["from 'svelte'", "svelte/store", "svelte/transition"],
    "nestjs":        ["@Module(", "@Controller(", "@Injectable()",
                      "from '@nestjs/", "NestFactory"],
    "koa":           ["require('koa')", "new Koa()", "from 'koa'"],
    "hapi":          ["require('@hapi/hapi')", "Hapi.server("],
    "fastify":       ["require('fastify')", "Fastify()", "from 'fastify'"],
    "remix":         ["from '@remix-run/", "loader(", "action("],
    "astro":         ["from 'astro'", "defineConfig", ".astro"],
    "gatsby":        ["from 'gatsby'", "gatsby-config", "graphql`"],
    "vite":          ["vite.config", "defineConfig", "from 'vite'", "vite"],
    "webpack":       ["webpack.config", "require('webpack')"],
    "electron":      ["require('electron')", "app.whenReady"],
    "graphql_js":    ["apollo-server", "ApolloServer(",
                      "typeDefs", "resolvers", "graphql-yoga"],
    "trpc":          ["from '@trpc/", "initTRPC", "createTRPCRouter"],
    "tailwind":      ["tailwind.config", "tailwindcss", "@tailwind base"],
    "prisma_js":     ["@prisma/client", "PrismaClient("],
    # Java / JVM
    "spring":        ["@SpringBootApplication", "@RestController",
                      "@RequestMapping", "springframework",
                      "@Service", "@Repository", "@Autowired"],
    "quarkus":       ["@QuarkusApplication", "import io.quarkus"],
    "micronaut":     ["@MicronautApplication", "import io.micronaut"],
    "ktor":          ["import io.ktor", "embeddedServer(", "routing {"],
    "android":       ["import android.", "AppCompatActivity", "import androidx."],
    # .NET
    "dotnet_mvc":    ["Microsoft.AspNetCore.Mvc", "IActionResult",
                      "[HttpGet]", "[HttpPost]", "ControllerBase"],
    "dotnet_blazor": ["Microsoft.AspNetCore.Components", "RenderFragment"],
    "dotnet_ef":     ["DbContext", "DbSet<", "OnModelCreating"],
    # Ruby
    "rails":         ["ActionController", "ActiveRecord", "ApplicationRecord",
                      "Rails.application"],
    "sinatra":       ["require 'sinatra'", "Sinatra::Base"],
    # PHP
    "laravel":       ["Illuminate\\", "artisan", "Route::get(", "Eloquent"],
    "symfony":       ["Symfony\\Component", "AbstractController"],
    "wordpress":     ["wp_enqueue_script", "add_action(", "get_permalink("],
    # Go
    "gin":           ['"github.com/gin-gonic/gin"', "gin.Default()", "gin.New()"],
    "echo_go":       ['"github.com/labstack/echo"', "echo.New()"],
    "fiber":         ['"github.com/gofiber/fiber"', "fiber.New()"],
    "grpc":          ["google.golang.org/grpc", "grpc.NewServer("],
    # Rust
    "actix":         ["actix_web", "HttpServer::new", "App::new()"],
    "axum":          ["use axum", "Router::new()", "axum::routing"],
    "rocket":        ["rocket::build()", "extern crate rocket"],
    # Mobile
    "react_native":  ["react-native", "from 'react-native'", "StyleSheet.create"],
    "flutter":       ["import 'package:flutter/", "StatelessWidget",
                      "StatefulWidget", "MaterialApp("],
    "ionic":         ["from '@ionic/", "IonContent", "IonPage"],
    "expo":          ["from 'expo'", "expo-", "Expo."],
    # Desktop
    "tauri":         ["from '@tauri-apps/", "tauri::Builder"],
    "qt":            ["#include <QApplication>", "QMainWindow", "import PyQt"],
    "tkinter":       ["import tkinter", "from tkinter", "Tk()"],
    # Cloud / IaC
    "aws_cdk":       ["from aws_cdk", "aws-cdk-lib", "Stack("],
    "pulumi":        ["import pulumi", "pulumi.export"],
}

# ── Database signatures ───────────────────────────────────────────────────
DATABASE_SIGNATURES = {
    "PostgreSQL":    ["psycopg2", "asyncpg", "postgresql", "pg.Pool",
                      "pg.Client", "postgres://", "dialect=postgresql"],
    "MySQL":         ["pymysql", "mysql-connector", "mysql2",
                      "mysql://", "dialect=mysql"],
    "SQLite":        ["sqlite3", "SQLite", "sqlite://", ":memory:"],
    "MongoDB":       ["pymongo", "mongoose", "MongoClient",
                      "mongodb://", "mongodb+srv://", "from motor", "beanie"],
    "Redis":         ["redis", "Redis(", "aioredis", "ioredis", "redis://"],
    "Elasticsearch": ["elasticsearch", "ElasticSearch(", "elastic.co"],
    "Cassandra":     ["cassandra", "CassandraDriver"],
    "DynamoDB":      ["boto3.resource('dynamodb')", "DynamoDB", "aws_dynamodb"],
    "Firestore":     ["firestore", "google.cloud.firestore"],
    "Supabase":      ["supabase", "from '@supabase/", "createClient"],
    "PlanetScale":   ["planetscale", "@planetscale/"],
    "CockroachDB":   ["cockroachdb", "cockroach://"],
    "Neo4j":         ["neo4j", "GraphDatabase", "bolt://"],
    "InfluxDB":      ["influxdb", "InfluxDBClient"],
    "Snowflake":     ["snowflake.connector", "snowflake-sqlalchemy"],
    "BigQuery":      ["google.cloud.bigquery", "from google.cloud import bigquery"],
    "SQLAlchemy":    ["sqlalchemy", "SQLAlchemy(", "create_engine(",
                      "declarative_base", "sessionmaker("],
    "Prisma":        ["PrismaClient", "@prisma/client"],
    "TypeORM":       ["typeorm", "DataSource(", "@Entity("],
    "Drizzle":       ["drizzle-orm", "from 'drizzle-orm'"],
    "Sequelize":     ["sequelize", "new Sequelize("],
    "Mongoose":      ["mongoose.model", "mongoose.Schema", "mongoose.connect"],
}

# ── Test framework signatures ─────────────────────────────────────────────
TEST_FRAMEWORK_SIGNATURES = {
    "pytest":      ["import pytest", "from pytest", "pytest.fixture",
                    "def test_", "pytest.mark"],
    "unittest":    ["import unittest", "TestCase", "self.assertEqual"],
    "hypothesis":  ["from hypothesis", "@given"],
    "jest":        ["describe(", "it(", "expect(", "jest.mock", "jest.config"],
    "vitest":      ["from 'vitest'", "vitest.config"],
    "mocha":       ["require('mocha')", "mocha.opts"],
    "cypress":     ["cy.", "cypress/", "Cypress."],
    "playwright":  ["@playwright/test", "test.describe", "page.goto("],
    "jasmine":     ["jasmine", "beforeAll("],
    "junit":       ["@Test", "import org.junit", "Assertions."],
    "testng":      ["import org.testng"],
    "rspec":       ["RSpec.describe", "expect(", ".to eq("],
    "gotest":      ["func Test", "testing.T", "t.Error("],
    "rust_test":   ["#[test]", "assert_eq!", "assert!("],
    "xunit":       ["[Fact]", "[Theory]", "Assert.Equal"],
    "nunit":       ["[Test]", "[TestFixture]", "Assert.That"],
}

# ── API endpoint patterns ─────────────────────────────────────────────────
API_PATTERNS = [
    "@app.get(", "@app.post(", "@app.put(", "@app.delete(", "@app.patch(",
    "@app.options(", "@app.route(",
    "@router.get(", "@router.post(", "@router.put(", "@router.delete(",
    "@router.patch(",
    "@blueprint.route(", "@bp.route(", "@api.route(", "@ns.route(",
    "path(\"",  "path('",
    "router.get(", "router.post(", "router.put(", "router.delete(",
    "router.patch(", "router.all(",
    "app.get(\"", "app.post(\"", "app.put(\"",
    "app.delete(\"", "app.patch(\"",
    "@GetMapping", "@PostMapping", "@PutMapping",
    "@DeleteMapping", "@PatchMapping", "@RequestMapping(",
    "[HttpGet]", "[HttpPost]", "[HttpPut]", "[HttpDelete]", "[HttpPatch]",
    ".GET(\"", ".POST(\"", ".PUT(\"", ".DELETE(\"", ".PATCH(\"",
    "@Get(", "@Post(", "@Put(", "@Delete(", "@Patch(",
    "#[get(", "#[post(", "#[put(", "#[delete(",
    "get {", "post {", "put {", "delete {",
]

# ── Manifest-based detection maps ────────────────────────────────────────
MANIFEST_FRAMEWORK_MAP = {
    "express": "express", "react": "react", "react-dom": "react",
    "next": "nextjs", "nuxt": "nuxtjs", "@angular/core": "angular",
    "vue": "vue", "@nestjs/core": "nestjs", "svelte": "svelte",
    "fastify": "fastify", "koa": "koa", "@hapi/hapi": "hapi",
    "electron": "electron", "@remix-run/react": "remix", "astro": "astro",
    "gatsby": "gatsby", "vite": "vite", "webpack": "webpack",
    "tailwindcss": "tailwind", "@prisma/client": "prisma_js",
    "typeorm": "typeorm", "sequelize": "sequelize", "mongoose": "mongoose",
    "drizzle-orm": "drizzle", "@trpc/server": "trpc",
    "graphql": "graphql_js", "react-native": "react_native",
    "expo": "expo", "@ionic/react": "ionic", "@tauri-apps/api": "tauri",
    "jest": "jest", "vitest": "vitest", "mocha": "mocha",
    "cypress": "cypress", "@playwright/test": "playwright",
}

MANIFEST_DB_MAP = {
    "pg": "PostgreSQL", "postgres": "PostgreSQL",
    "mysql": "MySQL", "mysql2": "MySQL",
    "sqlite3": "SQLite", "better-sqlite3": "SQLite",
    "mongodb": "MongoDB", "mongoose": "MongoDB",
    "redis": "Redis", "ioredis": "Redis",
    "@elastic/elasticsearch": "Elasticsearch",
    "@supabase/supabase-js": "Supabase",
    "firebase": "Firestore", "neo4j-driver": "Neo4j",
    "influxdb-client": "InfluxDB",
}

PYTHON_MANIFEST_FRAMEWORK_MAP = {
    "fastapi": "fastapi", "django": "django", "flask": "flask",
    "tornado": "tornado", "aiohttp": "aiohttp", "starlette": "starlette",
    "litestar": "litestar", "sanic": "sanic",
    "tensorflow": "tensorflow", "torch": "pytorch",
    "scikit-learn": "sklearn", "pandas": "pandas", "numpy": "numpy",
    "langchain": "langchain", "langgraph": "langgraph",
    "openai": "openai", "transformers": "huggingface", "celery": "celery",
    "pytest": "pytest", "hypothesis": "hypothesis",
    "boto3": "aws_cdk", "pulumi": "pulumi",
}

PYTHON_MANIFEST_DB_MAP = {
    "psycopg2": "PostgreSQL", "psycopg2-binary": "PostgreSQL",
    "asyncpg": "PostgreSQL", "pymysql": "MySQL",
    "mysql-connector-python": "MySQL",
    "pymongo": "MongoDB", "motor": "MongoDB", "beanie": "MongoDB",
    "redis": "Redis", "aioredis": "Redis",
    "elasticsearch": "Elasticsearch", "sqlalchemy": "SQLAlchemy",
    "cassandra-driver": "Cassandra", "boto3": "DynamoDB",
    "firebase-admin": "Firestore", "neo4j": "Neo4j",
    "influxdb-client": "InfluxDB",
    "snowflake-connector-python": "Snowflake",
    "google-cloud-bigquery": "BigQuery",
}


# ── File readers ──────────────────────────────────────────────────────────
def _read_safe(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _parse_package_json(filepath: str) -> tuple:
    frameworks, databases = set(), set()
    try:
        data = json.loads(_read_safe(filepath))
        all_deps = {}
        all_deps.update(data.get("dependencies", {}))
        all_deps.update(data.get("devDependencies", {}))
        for pkg in all_deps:
            if pkg in MANIFEST_FRAMEWORK_MAP:
                frameworks.add(MANIFEST_FRAMEWORK_MAP[pkg])
            if pkg in MANIFEST_DB_MAP:
                databases.add(MANIFEST_DB_MAP[pkg])
    except Exception:
        pass
    return frameworks, databases


def _parse_python_manifest(filepath: str) -> tuple:
    frameworks, databases = set(), set()
    content = _read_safe(filepath).lower()
    for pkg, fw in PYTHON_MANIFEST_FRAMEWORK_MAP.items():
        if pkg.lower() in content:
            frameworks.add(fw)
    for pkg, db in PYTHON_MANIFEST_DB_MAP.items():
        if pkg.lower() in content:
            databases.add(db)
    return frameworks, databases


def _parse_go_mod(filepath: str) -> set:
    frameworks = set()
    content = _read_safe(filepath)
    go_map = {
        "gin-gonic/gin": "gin", "labstack/echo": "echo_go",
        "gofiber/fiber": "fiber", "google.golang.org/grpc": "grpc",
    }
    for pattern, fw in go_map.items():
        if pattern in content:
            frameworks.add(fw)
    return frameworks


def _parse_pubspec(filepath: str) -> tuple:
    frameworks, databases = set(), set()
    content = _read_safe(filepath).lower()
    if "flutter" in content:
        frameworks.add("flutter")
    if "firebase_core" in content or "cloud_firestore" in content:
        databases.add("Firestore")
    return frameworks, databases


def _parse_pom_xml(filepath: str) -> set:
    frameworks = set()
    content = _read_safe(filepath)
    if "spring-boot" in content or "springframework" in content:
        frameworks.add("spring")
    if "quarkus" in content:
        frameworks.add("quarkus")
    if "micronaut" in content:
        frameworks.add("micronaut")
    return frameworks


def _parse_build_gradle(filepath: str) -> set:
    frameworks = set()
    content = _read_safe(filepath)
    if "spring" in content:
        frameworks.add("spring")
    if "io.ktor" in content:
        frameworks.add("ktor")
    if "com.android.application" in content:
        frameworks.add("android")
    return frameworks


def _parse_csproj(filepath: str) -> set:
    frameworks = set()
    content = _read_safe(filepath)
    if "AspNetCore" in content:
        frameworks.add("dotnet_mvc")
    if "Blazor" in content:
        frameworks.add("dotnet_blazor")
    if "EntityFrameworkCore" in content:
        frameworks.add("dotnet_ef")
    return frameworks


# ── MAIN ANALYZER ─────────────────────────────────────────────────────────
def analyze_codebase(filtered_files: List[str]) -> AnalysisResult:
    languages_found:       set = set()
    frameworks_found:      set = set()
    databases_found:       set = set()
    test_frameworks_found: set = set()
    api_count                  = 0
    total_loc                  = 0

    for filepath in filtered_files:
        filename  = os.path.basename(filepath).lower()
        _, ext    = os.path.splitext(filepath)
        ext_lower = ext.lower()

        # Language from extension
        lang = EXTENSION_TO_LANGUAGE.get(ext_lower)
        if lang:
            languages_found.add(lang)

        # LOC for source files
        if ext_lower in SOURCE_EXTENSIONS:
            content = _read_safe(filepath)
            if content:
                total_loc += content.count("\n") + 1
        else:
            content = _read_safe(filepath)

        if not content:
            continue

        content_lower = content.lower()

        # ── Manifest parsing (highest confidence) ─────────────────────────
        if filename == "package.json":
            fw, db = _parse_package_json(filepath)
            frameworks_found |= fw
            databases_found  |= db

        elif filename in ("requirements.txt", "pipfile", "pyproject.toml",
                          "setup.cfg", "setup.py", "poetry.lock"):
            fw, db = _parse_python_manifest(filepath)
            frameworks_found |= fw
            databases_found  |= db

        elif filename == "go.mod":
            frameworks_found |= _parse_go_mod(filepath)

        elif filename == "pubspec.yaml":
            fw, db = _parse_pubspec(filepath)
            frameworks_found |= fw
            databases_found  |= db

        elif filename == "pom.xml":
            frameworks_found |= _parse_pom_xml(filepath)

        elif filename in ("build.gradle", "build.gradle.kts"):
            frameworks_found |= _parse_build_gradle(filepath)

        elif ext_lower == ".csproj":
            frameworks_found |= _parse_csproj(filepath)

        # ── Content-based detection ────────────────────────────────────────
        for framework, sigs in FRAMEWORK_SIGNATURES.items():
            if any(sig.lower() in content_lower for sig in sigs):
                frameworks_found.add(framework)

        for db, sigs in DATABASE_SIGNATURES.items():
            if any(sig.lower() in content_lower for sig in sigs):
                databases_found.add(db)

        for tf, sigs in TEST_FRAMEWORK_SIGNATURES.items():
            if any(sig.lower() in content_lower for sig in sigs):
                test_frameworks_found.add(tf)

        for pattern in API_PATTERNS:
            api_count += content.count(pattern)

    # ── DevOps/infra detection ─────────────────────────────────────────────
    tech = detect_tech_stack(filtered_files)

    # ── Move test frameworks out of main frameworks list ───────────────────
    pure_test = {"jest", "vitest", "mocha", "cypress", "playwright",
                 "jasmine", "pytest", "hypothesis", "unittest",
                 "junit", "testng", "rspec", "gotest", "rust_test",
                 "xunit", "nunit"}
    test_frameworks_found |= (frameworks_found & pure_test)
    frameworks_found      -= pure_test

    # ── Drop config-only languages if real code exists ────────────────────
    config_only = {"YAML", "JSON", "TOML", "HTML", "CSS"}
    real_langs  = languages_found - config_only
    if real_langs:
        languages_found = real_langs

    return AnalysisResult(
        languages           = sorted(languages_found),
        frameworks          = sorted(frameworks_found),
        databases           = sorted(databases_found),
        test_frameworks     = sorted(test_frameworks_found),
        has_dockerfile      = tech["has_dockerfile"],
        has_cicd            = tech["has_cicd"],
        has_kubernetes      = tech["has_kubernetes"],
        has_terraform       = tech["has_terraform"],
        has_ansible         = tech["has_ansible"],
        api_endpoints_count = api_count,
        total_loc           = total_loc,
    )
