-- ============================================================
--  Student Freelancing Platform — MySQL Schema
--  Import: mysql -u root -p student_freelancing_db < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS student_freelancing_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE student_freelancing_db;

-- ── Django required tables ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS django_content_type (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  app_label       VARCHAR(100) NOT NULL,
  model           VARCHAR(100) NOT NULL,
  UNIQUE KEY django_content_type_app_label_model (app_label, model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS auth_permission (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  name            VARCHAR(255) NOT NULL,
  content_type_id INT NOT NULL,
  codename        VARCHAR(100) NOT NULL,
  UNIQUE KEY auth_permission_content_type_id_codename (content_type_id, codename),
  CONSTRAINT auth_permission_content_type_id_fk
    FOREIGN KEY (content_type_id) REFERENCES django_content_type (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS django_migrations (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  app         VARCHAR(255) NOT NULL,
  name        VARCHAR(255) NOT NULL,
  applied     DATETIME(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS django_session (
  session_key  VARCHAR(40)  NOT NULL PRIMARY KEY,
  session_data LONGTEXT     NOT NULL,
  expire_date  DATETIME(6)  NOT NULL,
  KEY django_session_expire_date (expire_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS django_admin_log (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  action_time     DATETIME(6)  NOT NULL,
  object_id       LONGTEXT,
  object_repr     VARCHAR(200) NOT NULL,
  action_flag     SMALLINT UNSIGNED NOT NULL,
  change_message  LONGTEXT     NOT NULL,
  content_type_id INT,
  user_id         BIGINT       NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── CustomUser ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS core_customuser (
  id           BIGINT AUTO_INCREMENT PRIMARY KEY,
  password     VARCHAR(128) NOT NULL,
  last_login   DATETIME(6),
  is_superuser TINYINT(1)   NOT NULL DEFAULT 0,
  username     VARCHAR(150) NOT NULL UNIQUE,
  first_name   VARCHAR(150) NOT NULL DEFAULT '',
  last_name    VARCHAR(150) NOT NULL DEFAULT '',
  email        VARCHAR(254) NOT NULL DEFAULT '',
  is_staff     TINYINT(1)   NOT NULL DEFAULT 0,
  is_active    TINYINT(1)   NOT NULL DEFAULT 1,
  date_joined  DATETIME(6)  NOT NULL,
  role         VARCHAR(10)  NOT NULL DEFAULT 'student'
    CHECK (role IN ('student','company','admin'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- User permissions M2M
CREATE TABLE IF NOT EXISTS core_customuser_groups (
  id           BIGINT AUTO_INCREMENT PRIMARY KEY,
  customuser_id BIGINT NOT NULL,
  group_id      INT    NOT NULL,
  UNIQUE KEY core_customuser_groups_uniq (customuser_id, group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS core_customuser_user_permissions (
  id              BIGINT AUTO_INCREMENT PRIMARY KEY,
  customuser_id   BIGINT NOT NULL,
  permission_id   INT    NOT NULL,
  UNIQUE KEY core_customuser_user_permissions_uniq (customuser_id, permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── StudentProfile ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS core_studentprofile (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id    BIGINT       NOT NULL UNIQUE,
  full_name  VARCHAR(200) NOT NULL,
  email      VARCHAR(254) NOT NULL,
  college    VARCHAR(300) NOT NULL,
  skills     LONGTEXT     NOT NULL,
  bio        LONGTEXT     NOT NULL DEFAULT '',
  phone      VARCHAR(15)  NOT NULL DEFAULT '',
  earnings   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  created_at DATETIME(6)  NOT NULL,
  CONSTRAINT core_studentprofile_user_fk
    FOREIGN KEY (user_id) REFERENCES core_customuser (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── CompanyProfile ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS core_companyprofile (
  id           BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id      BIGINT       NOT NULL UNIQUE,
  company_name VARCHAR(300) NOT NULL,
  email        VARCHAR(254) NOT NULL,
  industry     VARCHAR(200) NOT NULL DEFAULT '',
  website      VARCHAR(200) NOT NULL DEFAULT '',
  description  LONGTEXT     NOT NULL DEFAULT '',
  phone        VARCHAR(15)  NOT NULL DEFAULT '',
  is_approved  TINYINT(1)   NOT NULL DEFAULT 1,
  created_at   DATETIME(6)  NOT NULL,
  CONSTRAINT core_companyprofile_user_fk
    FOREIGN KEY (user_id) REFERENCES core_customuser (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Job ───────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS core_job (
  id              BIGINT AUTO_INCREMENT PRIMARY KEY,
  company_id      BIGINT       NOT NULL,
  title           VARCHAR(300) NOT NULL,
  description     LONGTEXT     NOT NULL,
  required_skills LONGTEXT     NOT NULL,
  budget          DECIMAL(10,2) NOT NULL,
  deadline        DATE         NOT NULL,
  status          VARCHAR(20)  NOT NULL DEFAULT 'open'
    CHECK (status IN ('open','in_progress','completed','closed')),
  category        VARCHAR(100) NOT NULL DEFAULT '',
  created_at      DATETIME(6)  NOT NULL,
  CONSTRAINT core_job_company_fk
    FOREIGN KEY (company_id) REFERENCES core_companyprofile (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Application ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS core_application (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  job_id     BIGINT      NOT NULL,
  student_id BIGINT      NOT NULL,
  proposal   LONGTEXT    NOT NULL,
  status     VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending','hired','rejected')),
  applied_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  UNIQUE KEY core_application_job_student (job_id, student_id),
  CONSTRAINT core_application_job_fk
    FOREIGN KEY (job_id) REFERENCES core_job (id) ON DELETE CASCADE,
  CONSTRAINT core_application_student_fk
    FOREIGN KEY (student_id) REFERENCES core_studentprofile (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Submission ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS core_submission (
  id             BIGINT AUTO_INCREMENT PRIMARY KEY,
  application_id BIGINT      NOT NULL UNIQUE,
  file           VARCHAR(100),
  notes          LONGTEXT    NOT NULL DEFAULT '',
  submitted_at   DATETIME(6) NOT NULL,
  CONSTRAINT core_submission_application_fk
    FOREIGN KEY (application_id) REFERENCES core_application (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Payment ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS core_payment (
  id             BIGINT AUTO_INCREMENT PRIMARY KEY,
  application_id BIGINT        NOT NULL UNIQUE,
  amount         DECIMAL(10,2) NOT NULL,
  status         VARCHAR(20)   NOT NULL DEFAULT 'not_paid'
    CHECK (status IN ('not_paid','paid')),
  paid_at        DATETIME(6),
  created_at     DATETIME(6)   NOT NULL,
  CONSTRAINT core_payment_application_fk
    FOREIGN KEY (application_id) REFERENCES core_application (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── PlatformSettings ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS core_platformsettings (
  id              BIGINT AUTO_INCREMENT PRIMARY KEY,
  commission_rate DECIMAL(5,2) NOT NULL DEFAULT 10.00,
  platform_rules  LONGTEXT     NOT NULL DEFAULT '',
  updated_at      DATETIME(6)  NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed default platform settings
INSERT INTO core_platformsettings (commission_rate, platform_rules, updated_at)
VALUES (10.00, 'Standard platform rules apply.\n1. All work must be original.\n2. Payments released only after submission review.\n3. Platform takes 10% commission.', NOW(6));

-- ============================================================
--  NOTE: After importing this schema, run Django migrations:
--    python manage.py migrate
--  This schema is for reference. Django's migrate command
--  will create the actual tables from models.py.
-- ============================================================
