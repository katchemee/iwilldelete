-- 1. SALES table with range partitions
CREATE TABLE sales (
  sale_id NUMBER,
  order_date DATE,
  amount NUMBER
)
PARTITION BY RANGE (order_date) (
  PARTITION p2024_01 VALUES LESS THAN (DATE '2024-02-01'),
  PARTITION p2024_02 VALUES LESS THAN (DATE '2024-03-01')
);

-- 2. ORDERS table with composite partitioning
CREATE TABLE orders (
  order_id NUMBER,
  order_date DATE,
  status VARCHAR2(20)
)
PARTITION BY RANGE (order_date)
SUBPARTITION BY LIST (status) (
  PARTITION p2024_01 VALUES LESS THAN (DATE '2024-02-01')
    (SUBPARTITION s_pending VALUES ('PENDING'),
     SUBPARTITION s_complete VALUES ('COMPLETE'))
);

-- 3. SAFE_DIVIDE function using SQLERRM
CREATE OR REPLACE FUNCTION safe_divide(p_num1 NUMBER, p_num2 NUMBER)
RETURN VARCHAR2
IS
  v_result NUMBER;
BEGIN
  v_result := p_num1 / p_num2;
  RETURN 'Result: ' || v_result;
EXCEPTION
  WHEN OTHERS THEN
    RETURN 'Error occurred: ' || SQLERRM;
END;
/

-- 4. CUSTOMER_LOG procedure using DBMS_OUTPUT
CREATE OR REPLACE PROCEDURE customer_log(p_customer_id NUMBER) IS
BEGIN
  DBMS_OUTPUT.PUT_LINE('Logging customer ' || p_customer_id);
END;
/

-- 5. PAYMENTS table with high-precision timestamp
CREATE TABLE payments (
  payment_id NUMBER,
  payment_time TIMESTAMP(9) WITH TIME ZONE,
  amount NUMBER
);

-- 6. REPORT_GEN procedure with dynamic SQL
CREATE OR REPLACE PROCEDURE report_gen(p_table_name VARCHAR2) IS
BEGIN
  EXECUTE IMMEDIATE 'SELECT COUNT(*) FROM ' || p_table_name;
END;
/

-- 7. PKG_UTILS package
CREATE OR REPLACE PACKAGE pkg_utils IS
  PROCEDURE util_proc;
END pkg_utils;
/

CREATE OR REPLACE PACKAGE BODY pkg_utils IS
  PROCEDURE util_proc IS
  BEGIN
    DBMS_OUTPUT.PUT_LINE('Utility procedure');
  END;
END pkg_utils;
/

-- 8. AUDIT_TRG trigger with autonomous transaction
CREATE OR REPLACE TRIGGER audit_trg
AFTER INSERT ON employees
DECLARE
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
  INSERT INTO audit_log (msg) VALUES ('Employee inserted');
  COMMIT;
END;
/

-- 9. EMP_SEQ sequence with NOCACHE
CREATE SEQUENCE emp_seq
  START WITH 1
  INCREMENT BY 1
  NOCACHE
  NOCYCLE;

-- 10. INVOICE_FUNC function using SYSDATE and ROWNUM
CREATE OR REPLACE FUNCTION invoice_func RETURN NUMBER IS
  v_id NUMBER;
BEGIN
  SELECT invoice_id INTO v_id
  FROM invoices
  WHERE ROWNUM = 1
  ORDER BY created_date DESC;

  DBMS_OUTPUT.PUT_LINE('Generated at ' || SYSDATE);
  RETURN v_id;
END;
/