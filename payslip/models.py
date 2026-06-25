from dataclasses import dataclass

PF_EMPLOYEE_RATE = 0.12
PF_EMPLOYER_RATE = 0.13
ESIC_EMPLOYEE_RATE = 0.0075
ESIC_EMPLOYER_RATE = 0.0325

PERMANENT = "Permanent"
LABOUR = "Labour"

STANDARD_DAYS = {
    PERMANENT: 26,
    LABOUR: 30,
}


def standard_days_for(employee_type: str) -> int:
    return STANDARD_DAYS.get(employee_type, STANDARD_DAYS[PERMANENT])


@dataclass
class Employee:
    name: str
    designation: str
    employee_id: str
    employee_type: str
    date_of_joining: str
    uan: str
    pay_days: float
    basic: float
    sp_allowance: float
    ptax: float


@dataclass
class PayslipResult:
    employee: Employee
    standard_days: int
    basic_earned: float
    sp_allowance_earned: float
    gross: float
    pf_employee: float
    pf_employer: float
    esic_employee: float
    esic_employer: float
    net: float
    ctc: float


def compute_payslip(employee: Employee) -> PayslipResult:
    standard_days = standard_days_for(employee.employee_type)
    attendance_ratio = min(employee.pay_days, standard_days) / standard_days

    basic_earned = round(employee.basic * attendance_ratio, 2)
    sp_allowance_earned = round(employee.sp_allowance * attendance_ratio, 2)
    gross = round(basic_earned + sp_allowance_earned, 2)

    pf_employee = round(basic_earned * PF_EMPLOYEE_RATE, 2)
    pf_employer = round(basic_earned * PF_EMPLOYER_RATE, 2)
    esic_employee = round(gross * ESIC_EMPLOYEE_RATE, 2)
    esic_employer = round(gross * ESIC_EMPLOYER_RATE, 2)
    net = round(gross - pf_employee - esic_employee - employee.ptax, 2)
    ctc = round(gross + pf_employer + esic_employer, 2)
    return PayslipResult(
        employee=employee,
        standard_days=standard_days,
        basic_earned=basic_earned,
        sp_allowance_earned=sp_allowance_earned,
        gross=gross,
        pf_employee=pf_employee,
        pf_employer=pf_employer,
        esic_employee=esic_employee,
        esic_employer=esic_employer,
        net=net,
        ctc=ctc,
    )
